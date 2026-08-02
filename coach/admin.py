from django.contrib import admin
from .models import CoachProfile, PlayerPerformance

@admin.register(CoachProfile)
class CoachProfileAdmin(admin.ModelAdmin):
    # This will let you see the coach's name and their linked club directly in a clear table layout
    list_display = ('id', 'full_name', 'phone_number')


@admin.register(PlayerPerformance)
class PlayerPerformanceAdmin(admin.ModelAdmin):
    list_display = ('id', 'player', 'coach', 'performance_date', 'match_title', 'goals', 'assists', 'rating')
    list_filter = ('performance_date', 'rating')
    search_fields = ('player__full_name', 'match_title', 'notes')
    date_hierarchy = 'performance_date'

