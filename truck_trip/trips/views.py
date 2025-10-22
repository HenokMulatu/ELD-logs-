from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.gis.geos import Point
from .serializers import TripInputSerializer, TripOutputSerializer
from .models import Trip, LogSheet
import requests
from geopy.geocoders import Nominatim
from datetime import datetime, timedelta
import json
import math  # For route interpolation

# Globals from settings (or hardcode for simplicity)
OSRM_BASE_URL = 'http://router.project-osrm.org'

geolocator = Nominatim(user_agent="truck_trip_app")

class CalculateTripView(APIView):
    def post(self, request):
        serializer = TripInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Geocode
        def geocode_address(addr):
            try:
                location = geolocator.geocode(addr, timeout=10)
                if not location:
                    raise ValueError(f"Invalid address: {addr}")
                return Point(location.longitude, location.latitude)
            except Exception as e:
                raise ValueError(f"Geocoding failed for {addr}: {str(e)}")

        current_pt = geocode_address(serializer.validated_data['current_location']['address'])
        pickup_pt = geocode_address(serializer.validated_data['pickup_location']['address'])
        dropoff_pt = geocode_address(serializer.validated_data['dropoff_location']['address'])

        # Create Trip
        trip = Trip.objects.create(
            current_location=current_pt,
            pickup_location=pickup_pt,
            dropoff_location=dropoff_pt,
            current_cycle_used=serializer.validated_data['current_cycle_used']
        )

        # Get route segments
        def get_route(start, end):
            url = f"{OSRM_BASE_URL}/route/v1/driving/{start.x},{start.y};{end.x},{end.y}?overview=full&alternatives=false&geometries=geojson"
            resp = requests.get(url, timeout=10)
            if resp.status_code != 200:
                raise ValueError(f"Routing failed: {resp.text}")
            data = resp.json()
            if 'routes' not in data or not data['routes']:
                raise ValueError("No route found")
            route = data['routes'][0]
            distance_meters = route['distance']
            distance_miles = distance_meters * 0.000621371
            time_seconds = route['duration']
            time_hours = time_seconds / 3600
            # Extract coordinates from geometry (polyline)
            coords_str = route['geometry']['coordinates']
            coords = [[coord[1], coord[0]] for coord in coords_str]  # [lat, lon]
            return distance_miles, time_hours, coords

        curr_to_pickup_dist, curr_to_pickup_time, curr_pickup_coords = get_route(current_pt, pickup_pt)
        pickup_to_drop_dist, pickup_to_drop_time, pickup_drop_coords = get_route(pickup_pt, dropoff_pt)
        total_dist = curr_to_pickup_dist + pickup_to_drop_dist
        total_drive_time = curr_to_pickup_time + pickup_to_drop_time
        total_on_duty = total_drive_time + 2  # +1hr each for pickup/dropoff

        # Fuel stops every 1000 miles (interpolate on pickup->dropoff route)
        fuel_stops = []
        route_coords = curr_pickup_coords + pickup_drop_coords[1:]  # Avoid duplicate pickup point
        if total_dist > 1000:
            num_fuels = math.floor(total_dist / 1000)
            for i in range(1, num_fuels + 1):
                stop_mile_from_start = i * 1000
                fraction = min(1.0, stop_mile_from_start / pickup_to_drop_dist)  # On main route
                idx = int(fraction * len(pickup_drop_coords))
                # Linear interpolate for precision
                if idx < len(pickup_drop_coords) - 1:
                    lat1, lon1 = pickup_drop_coords[idx]
                    lat2, lon2 = pickup_drop_coords[idx + 1]
                    interp_lat = lat1 + fraction * (lat2 - lat1)
                    interp_lon = lon1 + fraction * (lon2 - lon1)
                else:
                    interp_lat, interp_lon = pickup_drop_coords[-1]
                fuel_stops.append({
                    'mile': stop_mile_from_start,
                    'lat': interp_lat,
                    'lon': interp_lon,
                    'type': 'Fuel Stop (30 min on-duty not driving)'
                })

        # HOS Check: 70hr/8 days
        remaining_cycle = 70 - trip.current_cycle_used
        avg_daily_drive = 11  # Max drive per day
        estimated_days = max(1, math.ceil(total_drive_time / avg_daily_drive))
        estimated_total_hours = total_on_duty + (len(fuel_stops) * 0.5)  # Fuel time
        if estimated_total_hours > remaining_cycle or estimated_days > 8:
            trip.delete()  # Cleanup
            return Response({'error': f'Trip exceeds limits: {estimated_total_hours:.1f}hrs > {remaining_cycle} remaining, or {estimated_days} > 8 days'}, status=status.HTTP_400_BAD_REQUEST)

        # Generate logs: Simulate multi-day, with 14hr window, 10hr rest
        start_time = datetime.now()
        logs = []
        current_time = start_time
        day_num = 1
        remaining_drive_time = total_drive_time
        daily_drive = 0
        on_duty_today = 0

        while remaining_drive_time > 0 or day_num <= estimated_days:
            log_data = {}
            date = current_time.date()

            # Daily schedule: Drive up to 11hrs, on-duty up to 14hrs, then 10hr off
            daily_drive = min(11, remaining_drive_time)
            on_duty_today = daily_drive + 1 + 0.5 * len([s for s in fuel_stops if ...])  # Simplified
            off_duty_today = 24 - on_duty_today

            # Fill 24hr grid (assume start driving at 06:00)
            drive_start_hour = 6
            current_hour = drive_start_hour
            for hour in range(24):
                slot_start = current_time + timedelta(hours=hour)
                slot_end = slot_start + timedelta(hours=1)
                slot_key = f"{slot_start.strftime('%H:%M')}-{slot_end.strftime('%H:%M')}"

                if current_hour < drive_start_hour + daily_drive:
                    log_data[slot_key] = 'Driving'
                    current_hour += 1
                elif on_duty_today > daily_drive:  # On-duty not driving (pickup/fuel)
                    log_data[slot_key] = 'On-Duty Not Driving'
                    on_duty_today -= 1
                else:
                    log_data[slot_key] = 'Off-Duty'

            # Enforce 10hr rest after 14hr window (simplified override)
            if on_duty_today > 14:
                for h in range(22, 24):  # 10pm to 8am next day, but per day
                    slot_start = current_time + timedelta(hours=h)
                    slot_end = slot_start + timedelta(hours=1)
                    slot_key = f"{slot_start.strftime('%H:%M')}-{slot_end.strftime('%H:%M')}"
                    log_data[slot_key] = 'Sleeper Berth (10hr Off-Duty)'

            log = LogSheet.objects.create(
                trip=trip,
                day_number=day_num,
                date=date,
                log_data=log_data,
                total_on_duty=on_duty_today,
                total_driving=daily_drive,
                total_off_duty=off_duty_today
            )
            logs.append(log)

            remaining_drive_time -= daily_drive
            current_time += timedelta(days=1)
            day_num += 1

        # Update trip
        trip.total_distance = total_dist
        trip.total_driving_time = total_drive_time
        trip.save()

        # Output
        output_serializer = TripOutputSerializer(trip)
        output = {
            'trip': output_serializer.data,
            'route_coords': route_coords,  # [[lat, lon], ...] for React polyline
            'fuel_stops': fuel_stops,
            'rest_stops': [{'type': 'Mandatory 10hr Rest', 'after_drive_hours': 11, 'lat': pickup_drop_coords[-1][0], 'lon': pickup_drop_coords[-1][1]}],  # Simplified
            'estimated_days': estimated_days
        }

        return Response(output, status=status.HTTP_201_CREATED)