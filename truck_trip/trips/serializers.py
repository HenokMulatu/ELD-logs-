from rest_framework import serializers
from .models import Trip, LogSheet
from geopy.geocoders import Nominatim

geolocator = Nominatim(user_agent="truck_trip_app")

class LocationInputSerializer(serializers.Serializer):
    address = serializers.CharField()  # e.g., "New York, NY"

class TripInputSerializer(serializers.Serializer):
    current_location = LocationInputSerializer()
    pickup_location = LocationInputSerializer()
    dropoff_location = LocationInputSerializer()
    current_cycle_used = serializers.FloatField()

class TripOutputSerializer(serializers.ModelSerializer):
    logs = LogSheetSerializer(many=True, read_only=True)  # Nested logs

    class Meta:
        model = Trip
        fields = ['id', 'total_distance', 'total_driving_time', 'logs', 'created_at']
        depth = 1

class LogSheetSerializer(serializers.ModelSerializer):
    class Meta:
        model = LogSheet
        fields = '__all__'