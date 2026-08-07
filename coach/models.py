from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
import random


def get_club_active_lineup(club):
    """Shared helper: return (formation, slots) for a club's active lineup.

    Generic and intentionally player-agnostic so it can be reused by both the
    club-manager dashboard and the player dashboard. If the club has no active
    formation (nullable FK), returns (None, []).

    Personalization (e.g. "is this my slot?") is layered on top of the returned
    data by the caller, not baked in here.
    """
    if club is None:
        return None, []

    formation = getattr(club, 'active_formation', None)
    if formation is None:
        return None, []

    return formation, list(formation.slots.all())


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


# ==========================================
# FORMATION MODEL
# (A club's tactical lineup / formation, e.g. 4-3-3)
# ==========================================
class Formation(models.Model):
    FORMATION_TYPES = [
        ('4-3-3', '4-3-3'),
        ('4-4-2', '4-4-2'),
        ('3-5-2', '3-5-2'),
    ]

    club = models.ForeignKey(
        'clubs.Club',
        on_delete=models.CASCADE,
        related_name='formations'
    )
    formation_type = models.CharField(
        max_length=20,
        choices=FORMATION_TYPES,
        default='4-3-3',
        help_text="Formation shape, e.g. 4-3-3, 4-4-2, 3-5-2"
    )
    name = models.CharField(
        max_length=50,
        default='4-3-3',
        help_text="Formation name, e.g. 4-3-3"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.name} — {self.club.name}"


# ==========================================
# LINEUP SLOT MODEL
# (A single positioned slot on the pitch within a formation)
# ==========================================
class LineupSlot(models.Model):
    POSITION_HINTS = [
        ('goalkeeper', 'Goalkeeper'),
        ('defender', 'Defender'),
        ('midfielder', 'Midfielder'),
        ('forward', 'Forward'),
    ]

    formation = models.ForeignKey(
        Formation,
        on_delete=models.CASCADE,
        related_name='slots'
    )
    slot_key = models.CharField(
        max_length=20,
        help_text="Short key, e.g. GK, LB, CB1, ST"
    )
    label = models.CharField(
        max_length=50,
        help_text="Display name, e.g. Goalkeeper, Left-Back"
    )
    top = models.FloatField(help_text="Vertical position (0–100) %")
    left = models.FloatField(help_text="Horizontal position (0–100) %")
    position_hint = models.CharField(
        max_length=20,
        choices=POSITION_HINTS,
        default='midfielder'
    )
    player = models.ForeignKey(
        'players.Player',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lineup_slots'
    )
    auto_assigned = models.BooleanField(
        default=False,
        help_text="True when this slot was filled automatically by the smart-defaults logic on build"
    )

    class Meta:
        ordering = ['slot_key']
        constraints = [
            models.UniqueConstraint(
                fields=['formation', 'slot_key'],
                name='unique_slot_per_formation'
            ),
            # Database-level guarantee that one player can never occupy two
            # slots in the same formation, even under race conditions or via
            # code paths that bypass the assign_slot view.
            #
            # NOTE: This is intentionally a plain (unconditional) unique
            # constraint. In standard SQL (and MariaDB/MySQL, PostgreSQL,
            # SQLite) NULL values are never considered equal to one another,
            # so this permits unlimited empty slots (player=NULL) per
            # formation while still rejecting two filled slots that point to
            # the same player. MariaDB does NOT support conditional unique
            # constraints (Django model W036), so we must NOT use
            # condition=Q(player__isnull=False) here.
            models.UniqueConstraint(
                fields=['formation', 'player'],
                name='unique_player_per_formation'
            ),
        ]

    def __str__(self):
        return f"{self.formation.name} — {self.label} ({self.slot_key})"
