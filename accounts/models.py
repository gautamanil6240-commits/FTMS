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

    phone_number = models.CharField(
        max_length=15,
        blank=True,
        null=True
    )

    profile_photo = models.ImageField(
        upload_to='profiles/',
        blank=True,
        null=True
    )

    def __str__(self):

        return self.username