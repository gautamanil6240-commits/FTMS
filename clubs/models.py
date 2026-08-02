from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

# ==========================================
# 1. CLUB MODEL
# ==========================================
class Club(models.Model):
    manager = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='managed_club'
    )
    name = models.CharField(max_length=150, unique=True)
    city = models.CharField(max_length=150, blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    logo = models.ImageField(upload_to='club_logos/', blank=True, null=True)
    
    # Official Verification Documents
    pan_document = models.FileField(upload_to='club_documents/pan/', blank=True, null=True)
    government_document = models.FileField(upload_to='club_documents/govt/', blank=True, null=True)
    citizenship_document = models.FileField(upload_to='club_documents/citizenship/', blank=True, null=True)
    
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

# ==========================================
# 2. COACH MODEL
# ==========================================
class Coach(models.Model):
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='club_coach_profile',
        null=True, blank=True
    )
    club = models.ForeignKey(
        Club, 
        on_delete=models.CASCADE, 
        related_name='club_coaches'
    )
    full_name = models.CharField(max_length=255)
    license_level = models.CharField(max_length=50, blank=True, null=True)
    coach_id_number = models.CharField(max_length=100, unique=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    
    def __str__(self):
        return f"Coach: {self.full_name} - {self.club.name}"

# ==========================================
# 3. PLAYER MODEL
# ==========================================
class Player(models.Model):
    coach = models.ForeignKey(
        Coach, 
        on_delete=models.CASCADE, 
        related_name='players'
    )
    full_name = models.CharField(max_length=150)
    jersey_number = models.PositiveIntegerField()
    position = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.full_name} (#{self.jersey_number})"