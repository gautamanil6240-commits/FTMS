from django.db import models
import uuid
from django.contrib.auth import get_user_model
from datetime import date
 
User = get_user_model()
 
class Player(models.Model):
 
    POSITION_CHOICES = [
        ('goalkeeper', 'Goalkeeper'),
        ('defender', 'Defender'),
        ('midfielder', 'Midfielder'),
        ('forward', 'Forward'),
    ]
 
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]
 
    MEDICAL_CHOICES = [
        ('fit', 'Fit'),
        ('injured', 'Injured'),
        ('suspended', 'Suspended'),
    ]
 
    # --- Unique ID ---
    player_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )
 
    # --- Link to Club ---
    club = models.ForeignKey(
        'clubs.Club',
        on_delete=models.CASCADE,
        related_name='players'
    )
 
    # --- Personal Info ---
    full_name = models.CharField(max_length=150, default='Unknown Player')
 
    profile_photo = models.ImageField(
        upload_to='player_profile_pics/',
        blank=True,
        null=True
    )
 
    date_of_birth = models.DateField(blank=True, null=True)
 
    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        default='male'
    )
 
    nationality = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
 
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )
 
    email = models.EmailField(
        blank=True,
        null=True
    )
 
    citizenship_document = models.FileField(
        upload_to='player_documents/',
        blank=True,
        null=True
    )
 
    # --- Football Info ---
    preferred_position = models.CharField(
        max_length=20,
        choices=POSITION_CHOICES,
        default='midfielder'
    )
 
    # ✅ Renamed from jersey_number to preferred_jersey_number
    preferred_jersey_number = models.PositiveIntegerField(
        blank=True,
        null=True
    )
 
    height = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        help_text='Height in cm'
    )
 
    weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        help_text='Weight in kg'
    )
 
    # --- Medical & Status ---
    medical_status = models.CharField(
        max_length=20,
        choices=MEDICAL_CHOICES,
        default='fit'
    )
 
    # --- Timestamps ---
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
 
    # --- Helper Properties ---
    @property
    def age(self):
        """Safely calculates player age, returning N/A if date_of_birth is missing"""
        if not self.date_of_birth:
            return "N/A"
 
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
 
    def __str__(self):
        return f"{self.full_name} ({self.preferred_position.capitalize()})"