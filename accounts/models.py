from django.db import models

from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):

    ROLE_CHOICES = (

        ('admin', 'Software Admin'),

        ('organizer', 'Tournament Organizer'),

        ('manager', 'Club Manager'),

        ('coach', 'Coach'),

        ('player', 'Player'),

        ('viewer', 'Viewer'),

    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES
    )

    approved = models.BooleanField(
        default=False
    )

    is_verified = models.BooleanField(
        default=False
    )

    # =====================
    # BASIC INFORMATION
    # =====================

    phone_number = models.CharField(
        max_length=15,
        blank=True,
        null=True
    )

    address = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    profile_photo = models.ImageField(
        upload_to='profiles/',
        blank=True,
        null=True
    )

    # =====================
    # CLUB DETAILS
    # =====================

    club_name = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    club_city = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    club_logo = models.ImageField(
        upload_to='club_logos/',
        blank=True,
        null=True
    )

    # =====================
    # DOCUMENTS
    # =====================

    pan_document = models.FileField(
        upload_to='documents/pan/',
        blank=True,
        null=True
    )

    government_document = models.FileField(
        upload_to='documents/government/',
        blank=True,
        null=True
    )

    citizenship_document = models.FileField(
        upload_to='documents/citizenship/',
        blank=True,
        null=True
    )

    # =====================
    # PLAYER STATUS
    # =====================

    is_active_player = models.BooleanField(
        default=True
    )

    injured = models.BooleanField(
        default=False
    )

    suspension_matches = models.IntegerField(
        default=0
    )

    def __str__(self):

        return self.username