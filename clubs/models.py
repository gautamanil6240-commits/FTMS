from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Club(models.Model):
    # Links the club directly to the logged-in Manager user account
    manager = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='managed_club'
    )
    
    # Matching your exact form fields from the screenshot:
    name = models.CharField(max_length=150, unique=True)
    founded_year = models.PositiveIntegerField(blank=True, null=True)
    pan_number = models.CharField(max_length=50, blank=True, null=True)  # Added from your screenshot
    logo = models.ImageField(upload_to='team_logos/', blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    
    # Document upload for the verification file input at the bottom
    government_registration = models.FileField(upload_to='authorization_letters/', blank=True, null=True)
    
    # Internal status tracking for your dashboard verification badge
    is_verified = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name