from django.contrib import admin
from .models import Tournament


@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):

    list_display = (
        'name',
        'organizer',
        'status',
        'start_date',
        'end_date'
    )

    list_filter = (
        'status',
        'format'
    )

    search_fields = (
        'name',
        'location'
    )