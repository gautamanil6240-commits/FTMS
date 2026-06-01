from django.db import models
from django.contrib.auth import get_user_model
from clubs.models import Club

User = get_user_model()

class Player(models.Model):
    # Connects to the main user account for login, name, email
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='player_profile')
    
    # Connects the player to a specific Club
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='players')
    
    # Player specific attributes for the roster
    jersey_number = models.PositiveIntegerField(blank=True, null=True)
    position = models.CharField(max_length=50, choices=[
        ('Goalkeeper', 'Goalkeeper'),
        ('Defender', 'Defender'),
        ('Midfielder', 'Midfielder'),
        ('Forward', 'Forward'),
    ], default='Midfielder')
    
    medical_status = models.CharField(max_length=20, choices=[
        ('FIT', 'Fit / Available'),
        ('INJURED', 'Injured / Unavailable'),
    ], default='FIT')

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"#{self.jersey_number or '--'} Player"