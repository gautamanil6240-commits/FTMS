from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist

User = get_user_model()


def get_or_create_manager_club(user):
    """
    Return the Club managed by *user*.
    If the Club record is missing (e.g. because the user registered via
    the generic accounts.register() view which only creates a UserProfile),
    create it automatically from the UserProfile data.
    """
    try:
        return user.managed_club
    except (ObjectDoesNotExist, AttributeError):
        try:
            profile = user.userprofile
        except (ObjectDoesNotExist, AttributeError):
            return None
        if profile.role != 'manager' or not profile.club_name:
            return None
        # Auto-create the missing Club record from UserProfile data
        club = Club.objects.create(
            manager=user,
            name=profile.club_name,
            city=profile.club_address or '',
            phone=profile.phone_number or '',
            logo=profile.club_logo if profile.club_logo else None,
            pan_document=None,   # documents are stored on UserProfile only
            government_document=None,
            citizenship_document=None,
            is_verified=profile.is_verified,
        )
        return club

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

    # The formation currently in use by the club. This is a separate FK
    # (rather than the historical OneToOne) so a club can keep multiple
    # Formation rows (active + historical snapshots) and switch between them.
    active_formation = models.ForeignKey(
        'coach.Formation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
        help_text="The formation currently in use by this club"
    )

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
