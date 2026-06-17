from django.contrib import admin
from .models import Player

@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    # 'get_username' points to the method below
    list_display = ('id', 'get_username', 'club') 

    def get_username(self, obj):
        # This safely checks if there's a related user object attached, whatever the field name is
        if hasattr(obj, 'user') and obj.user:
            return obj.user.username
        elif hasattr(obj, 'user_profile') and obj.user_profile:
            return obj.user_profile.username
        
        # Fallback if there is a direct text field or no relation
        return getattr(obj, 'full_name', 'No linked account')
        
    # Sets the column header title in the admin panel
    get_username.short_description = 'Account Username'