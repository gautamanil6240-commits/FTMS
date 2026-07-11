from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator

class CoachProfile(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    # Links back to Account Details (Username, Password, Email)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='coach_profile')

    club = models.OneToOneField('clubs.Club', on_delete=models.SET_NULL, null=True, blank=True, related_name='manager_profile')

    # Personal Information
    # Note: User model holds first_name/last_name natively, but a dedicated full_name field keeps profile renders easy
    full_name = models.CharField(max_length=150)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    nationality = models.CharField(max_length=100)
    profile_photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True)

    # Contact Information
    # Email is managed natively via user.email; Phone gets rigorous formatting guards
    phone_regex = RegexValidator(
        regex=r'^\d{10}$',
        message="Phone number must be exactly 10 digits."
    )
    phone_number = models.CharField(validators=[phone_regex], max_length=10)

    # Qualifications
    education = models.CharField(max_length=255, blank=True, null=True)
    coaching_license = models.CharField(max_length=100, blank=True, null=True)
    certificates = models.FileField(upload_to='coaches/documents/', blank=True, null=True)

    def __str__(self):
        return f"Coach: {self.full_name} ({self.user.username})"