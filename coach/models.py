from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
import random

class CoachProfile(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    # Links back to Account Details (Username, Password, Email)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='coach_profile')

    club = models.ForeignKey('clubs.Club', on_delete=models.SET_NULL, null=True, blank=True, related_name='coaches')

    # Unique Coach ID (Added to support unique identifiers like coa65674)
    coach_id_number = models.CharField(max_length=20, unique=True, blank=True, null=True)

    # Personal Information
    full_name = models.CharField(max_length=150)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True)
    nationality = models.CharField(max_length=100, blank=True, null=True)
    profile_photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True)

    # Contact Information
    phone_regex = RegexValidator(
        regex=r'^\d{10}$',
        message="Phone number must be exactly 10 digits."
    )
    phone_number = models.CharField(validators=[phone_regex], max_length=10, blank=True, null=True)

    # Qualifications
    education = models.CharField(max_length=255, blank=True, null=True)
    coaching_license = models.CharField(max_length=100, blank=True, null=True)
    certificates = models.FileField(upload_to='coaches/documents/', blank=True, null=True)

    def save(self, *args, **kwargs):
        # Automatically generate a unique coach ID if it doesn't exist (e.g., coa65674)
        if not self.coach_id_number:
            while True:
                random_num = random.randint(10000, 99999)
                generated_id = f"coa{random_num}"
                if not CoachProfile.objects.filter(coach_id_number=generated_id).exists():
                    self.coach_id_number = generated_id
                    break
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Coach: {self.full_name} ({self.coach_id_number or self.user.username})"


# ==========================================
# PLAYER PERFORMANCE MODEL
# (Coaches log per-match stats & periodic reviews for players)
# ==========================================
class PlayerPerformance(models.Model):
    RATING_CHOICES = [(i, f"{i} / 10") for i in range(1, 11)]

    # Who the record belongs to and who logged it
    player = models.ForeignKey(
        'players.Player',
        on_delete=models.CASCADE,
        related_name='performance_records'
    )
    coach = models.ForeignKey(
        CoachProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='logged_performances',
        help_text="Coach who logged this performance record"
    )

    # Match / Review Info
    performance_date = models.DateField()
    match_title = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Opponent or match description (e.g. vs. FC Eagles)"
    )

    # Per-match stats
    goals = models.PositiveIntegerField(default=0)
    assists = models.PositiveIntegerField(default=0)
    minutes_played = models.PositiveIntegerField(blank=True, null=True)

    # Rating & coach notes
    rating = models.PositiveIntegerField(
        choices=RATING_CHOICES,
        blank=True,
        null=True,
        help_text="Performance rating from 1 (poor) to 10 (outstanding)"
    )
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Coach comments, fitness notes, tactical observations..."
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-performance_date', '-created_at']

    def __str__(self):
        return f"{self.player.full_name} — {self.performance_date}"
