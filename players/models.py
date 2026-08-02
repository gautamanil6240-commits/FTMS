from django.db import models
import random
from django.contrib.auth import get_user_model
from datetime import date
from django.core.validators import RegexValidator
 
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
 
    # --- Unique ID (6-digit) ---
    player_id = models.CharField(
        max_length=6,
        unique=True,
        editable=False,
        blank=True
    )
 
    # --- Link to Club ---
    club = models.ForeignKey(
        'clubs.Club',
        on_delete=models.SET_NULL, 
        related_name='players',
        null=True,                
        blank=True                
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

    phone_validator = RegexValidator(
        regex=r'^\d{10}$',
        message="Phone number must be exactly 10 digits (e.g., 9876543210)."
    )
 
    phone_number = models.CharField(
        max_length=10,
        validators=[phone_validator],
        help_text="Enter a 10-digit mobile number",
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
 
# --- Auto-generate 6-digit unique ID ---
    def save(self, *args, **kwargs):
        if not self.player_id:
            while True:
                code = str(random.randint(100000, 999999))
                if not Player.objects.filter(player_id=code).exists():
                    self.player_id = code
                    break
        super().save(*args, **kwargs)

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

    def performance_chart_data(self):
        """Builds Chart.js-ready datasets from this player's performance records.

        Returns raw Python lists/dicts — templates embed them safely with the
        ``json_script`` template tag. Includes labels, goals, assists, minutes,
        ratings, plus a rating-distribution pie and a goals-vs-assists pie.
        """
        records = list(self.performance_records.all())

        labels = [r.performance_date.strftime('%d %b') for r in records]
        goals = [r.goals for r in records]
        assists = [r.assists for r in records]
        minutes = [r.minutes_played or 0 for r in records]
        ratings = [r.rating or 0 for r in records]

        # Rating distribution (1–10) for the pie chart
        rating_counts = {str(i): 0 for i in range(1, 11)}
        for r in records:
            if r.rating:
                rating_counts[str(r.rating)] += 1

        # Goals vs. Assists contribution pie
        total_goals = sum(goals)
        total_assists = sum(assists)

        return {
            'has_data': bool(records),
            'labels': labels,
            'goals': goals,
            'assists': assists,
            'minutes': minutes,
            'ratings': ratings,
            'rating_pie': {
                'labels': list(rating_counts.keys()),
                'values': list(rating_counts.values()),
            },
            'contribution_pie': {
                'labels': ['Goals', 'Assists'],
                'values': [total_goals, total_assists],
            },
        }
 
    def __str__(self):
        return f"{self.full_name} ({self.preferred_position.capitalize()})"


class PlayerAchievement(models.Model):
    player = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        related_name='achievements'
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    photo = models.ImageField(
        upload_to='player_achievements/',
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.player.full_name}"
