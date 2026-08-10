from django.db import models
from django.conf import settings
from clubs.models import Club


class Tournament(models.Model):

    FORMAT_CHOICES = [
        ('league', 'League'),
        ('knockout', 'Knockout'),
        ('group_ko', 'Group + Knockout'),
    ]

    STATUS_CHOICES = [
        ('registration', 'Registration Open'),
        ('active', 'Active'),
        ('upcoming', 'Upcoming'),
        ('completed', 'Completed'),
    ]

    REGISTRATION_TYPE_CHOICES = [
        ('pre', 'Pre-Registration Only'),
        ('open', 'Open Registration'),
        ('invite', 'Invitation Only'),
    ]

    AGE_CATEGORY_CHOICES = [
        ('all', 'Open (All Ages)'),
        ('u13', 'Under-13 (U13)'),
        ('u15', 'Under-15 (U15)'),
        ('u19', 'Under-19 (U19)'),
        ('u23', 'Under-23 (U23)'),
        ('u25', 'Under-25 (U25)'),
    ]

    GENDER_CATEGORY_CHOICES = [
        ('men', "Men's Tournament"),
        ('women', "Women's Tournament"),
        ('mixed', 'Mixed Category'),
    ]

    organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    name = models.CharField(max_length=255)

    description = models.TextField(blank=True)

    location = models.CharField(max_length=255)

    banner = models.ImageField(
        upload_to='tournaments/',
        blank=True,
        null=True
    )

    start_date = models.DateField()
    end_date = models.DateField()

    format = models.CharField(
        max_length=20,
        choices=FORMAT_CHOICES
    )

    max_teams = models.IntegerField()

    players_per_team = models.IntegerField()

    # ===== Contact & Administration =====
    contact_person = models.CharField(
        max_length=255,
        blank=True
    )

    phone = models.CharField(
        max_length=20,
        blank=True
    )

    registration_type = models.CharField(
        max_length=20,
        choices=REGISTRATION_TYPE_CHOICES,
        default='open'
    )

    # ===== Category Rules =====
    age_category = models.CharField(
        max_length=20,
        choices=AGE_CATEGORY_CHOICES,
        default='all'
    )

    gender_category = models.CharField(
        max_length=20,
        choices=GENDER_CATEGORY_CHOICES,
        default='men'
    )

    # ===== Schedule & Deadlines =====
    registration_deadline = models.DateField(
        blank=True,
        null=True
    )

    # ===== Prize & Awards =====
    prize_first = models.CharField(
        max_length=100,
        blank=True
    )

    prize_second = models.CharField(
        max_length=100,
        blank=True
    )

    prize_third = models.CharField(
        max_length=100,
        blank=True
    )

    # Extra physical awards & medals (details text; empty = not awarded)
    award_trophy = models.CharField(
        max_length=255,
        blank=True
    )

    award_medals = models.CharField(
        max_length=255,
        blank=True
    )

    award_certificate = models.CharField(
        max_length=255,
        blank=True
    )

    award_best_player = models.CharField(
        max_length=255,
        blank=True
    )

    award_top_scorer = models.CharField(
        max_length=255,
        blank=True
    )

    award_best_goalkeeper = models.CharField(
        max_length=255,
        blank=True
    )

    award_fair_play = models.CharField(
        max_length=255,
        blank=True
    )

    rules = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='registration'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def teams_count(self):
        return self.registrations.filter(status='approved').count()

    def __str__(self):
        return self.name


class TournamentRegistration(models.Model):

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE,
        related_name='registrations'
    )

    club = models.ForeignKey(
        Club,
        on_delete=models.CASCADE,
        related_name='tournament_registrations'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    registered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tournament_registrations'
    )

    registered_at = models.DateTimeField(auto_now_add=True)

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_registrations'
    )

    reviewed_at = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['tournament', 'club'],
                name='unique_tournament_club'
            )
        ]

    def __str__(self):
        return f"{self.club.name} → {self.tournament.name} ({self.status})"
