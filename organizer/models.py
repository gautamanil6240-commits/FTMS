from django.db import models
from django.conf import settings

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

    rules = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='registration'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
    @property
    def teams_count(self):
        return 0

    def __str__(self):
        return self.name    