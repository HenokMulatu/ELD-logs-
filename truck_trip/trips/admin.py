from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin
from .models import Trip, LogSheet

@admin.register(Trip)
class TripAdmin(OSMGeoAdmin):
    list_display = ['id', 'total_distance', 'total_driving_time', 'created_at']

@admin.register(LogSheet)
class LogSheetAdmin(admin.ModelAdmin):
    list_display = ['trip', 'day_number', 'date', 'total_driving']