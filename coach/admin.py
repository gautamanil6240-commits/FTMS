from django.contrib import admin
from .models import CoachProfile

@admin.register(CoachProfile)
class CoachProfileAdmin(admin.ModelAdmin):
    # This will let you see the coach's name and their linked club directly in a clear table layout
    list_display = ('id', 'full_name', 'phone_number')