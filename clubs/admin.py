# Example for registering a Club/Team model if it exists
from django.contrib import admin
from .models import Club  # adjust this import to point to your actual club model location

admin.site.register(Club)