from django.db import models
from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import Point

class Trip(models.Model):
    current_location = gis_models.PointField(null=True, blank=True)  # Will set after geocoding
    pickup_location = gis_models.PointField(null=True, blank=True)
    dropoff_location = gis_models.PointField(null=True, blank=True)
    current_cycle_used = models.FloatField(default=0)  # Hours used in current 8-day cycle
    total_distance = models.FloatField(null=True, blank=True)  # Miles
    total_driving_time = models.FloatField(null=True, blank=True)  # Hours
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Trip ID {self.id}: {self.pickup_location} to {self.dropoff_location}"

class LogSheet(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='logs')
    day_number = models.IntegerField()  # Day 1, 2, etc.
    date = models.DateField()
    log_data = models.JSONField(default=dict)  # {'14:00-15:00': 'Driving', ...}
    total_on_duty = models.FloatField(default=0)
    total_driving = models.FloatField(default=0)
    total_off_duty = models.FloatField(default=0)

    def __str__(self):
        return f"Log Day {self.day_number} for Trip {self.trip.id}"