from django.db import models
from django.contrib.auth.models import User
import uuid


class UserProfile(models.Model):

    ROLE_CHOICES = (
        ('organizer', 'Organizer'),
        ('manager', 'Manager'),
        ('coach', 'Coach'),
        ('player', 'Player'),
        ('viewer', 'Viewer'),
    )

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES
    )

    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    profile_photo = models.ImageField(
        upload_to='profile_photos/',
        blank=True,
        null=True
    )

    is_verified = models.BooleanField(default=False)

    # =========================
    # ORGANIZER
    # =========================

    organization_name = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    pan_number = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    organizer_logo = models.ImageField(
        upload_to='organizer_logos/',
        blank=True,
        null=True
    )

    authorization_letter = models.FileField(
        upload_to='authorization_letters/',
        blank=True,
        null=True
    )

    tournament_name = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    office_address = models.TextField(
        blank=True,
        null=True
    )

    # =========================
    # MANAGER
    # =========================

    club_name = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    founded_year = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    club_logo = models.ImageField(
        upload_to='club_logos/',
        blank=True,
        null=True
    )

    government_registration = models.FileField(
        upload_to='government_registration/',
        blank=True,
        null=True
    )

    club_address = models.TextField(
        blank=True,
        null=True
    )

# =========================
    # COACH
    # =========================
    
    assigned_manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='club_coaches',
        limit_choices_to={'userprofile__role': 'manager'}
    )

    coach_id_number = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True
    )
    
    coach_license = models.FileField(
        upload_to='coach_license/',
        blank=True,
        null=True
    )

    experience_certificate = models.FileField(
        upload_to='experience_certificates/',
        blank=True,
        null=True
    )

    citizenship_document = models.FileField(
        upload_to='citizenship_documents/',
        blank=True,
        null=True
    )

    # =========================
    # PLAYER
    # =========================

    date_of_birth = models.DateField(
        blank=True,
        null=True
    )

    jersey_number = models.CharField(
        max_length=10,
        blank=True,
        null=True
    )

    preferred_position = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    medical_status = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if self.role == 'coach' and not self.coach_id_number:
            self.coach_id_number = f"COACH-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.user.username