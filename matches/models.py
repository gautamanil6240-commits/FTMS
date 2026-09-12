from django.core.exceptions import ValidationError
from django.db import models


class Match(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    NEXT_MATCH_SLOT_CHOICES = [
        ('home', 'Home'),
        ('away', 'Away'),
    ]

    tournament = models.ForeignKey(
        'organizer.Tournament',
        on_delete=models.CASCADE,
        related_name='matches'
    )
    home_team = models.ForeignKey(
        'clubs.Club',
        on_delete=models.CASCADE,
        related_name='home_matches',
        null=True,
        blank=True,
    )
    away_team = models.ForeignKey(
        'clubs.Club',
        on_delete=models.CASCADE,
        related_name='away_matches',
        null=True,
        blank=True,
    )
    home_score = models.IntegerField(blank=True, null=True)
    away_score = models.IntegerField(blank=True, null=True)
    penalty_home_score = models.IntegerField(blank=True, null=True)
    penalty_away_score = models.IntegerField(blank=True, null=True)
    match_date = models.DateTimeField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='scheduled'
    )
    round_number = models.PositiveIntegerField(
        default=1,
        help_text="Bracket round (1 = first round, 2 = next, etc.)"
    )
    next_match = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='feeder_matches',
        help_text="The match whose slot the winner of this match fills",
    )
    next_match_slot = models.CharField(
        max_length=4,
        choices=NEXT_MATCH_SLOT_CHOICES,
        blank=True,
        default='',
        help_text="Which side of next_match the winner fills: 'home' or 'away'",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['round_number', 'match_date', 'id']

    def clean(self):
        super().clean()
        if self.home_team_id and self.away_team_id and self.home_team_id == self.away_team_id:
            raise ValidationError('A match cannot be played between the same club.')

    def __str__(self):
        if self.home_team and self.away_team:
            return f"{self.home_team.name} vs {self.away_team.name}"
        if self.home_team:
            return f"{self.home_team.name} vs TBD"
        if self.away_team:
            return f"TBD vs {self.away_team.name}"
        return "TBD vs TBD"


class Goal(models.Model):
    match = models.ForeignKey(
        Match,
        on_delete=models.CASCADE,
        related_name='goals'
    )
    player = models.ForeignKey(
        'players.Player',
        on_delete=models.CASCADE,
        related_name='match_goals'
    )
    team = models.ForeignKey(
        'clubs.Club',
        on_delete=models.CASCADE,
        related_name='goals_scored'
    )
    minute = models.PositiveIntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['minute', 'id']

    def clean(self):
        super().clean()
        if not self.match_id:
            return
        valid_clubs = {self.match.home_team_id, self.match.away_team_id}
        if self.player_id and self.player.club_id not in valid_clubs:
            raise ValidationError('This player does not belong to either club in this match.')
        if self.team_id and self.team_id not in valid_clubs:
            raise ValidationError('This goal cannot be credited to a club not playing in this match.')

    def __str__(self):
        return f"{self.player} ({self.team.name})"


class Card(models.Model):
    CARD_CHOICES = [
        ('yellow', 'Yellow'),
        ('red', 'Red'),
    ]

    match = models.ForeignKey(
        Match,
        on_delete=models.CASCADE,
        related_name='cards'
    )
    player = models.ForeignKey(
        'players.Player',
        on_delete=models.CASCADE,
        related_name='match_cards'
    )
    card_type = models.CharField(
        max_length=10,
        choices=CARD_CHOICES,
        default='yellow'
    )
    minute = models.PositiveIntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['minute', 'id']

    def clean(self):
        super().clean()
        if not self.match_id:
            return
        valid_clubs = {self.match.home_team_id, self.match.away_team_id}
        if self.player_id and self.player.club_id not in valid_clubs:
            raise ValidationError('This player does not belong to either club in this match.')

    def __str__(self):
        return f"{self.player} - {self.card_type.title()} card"


class Substitution(models.Model):
    match = models.ForeignKey(
        Match,
        on_delete=models.CASCADE,
        related_name='substitutions'
    )
    team = models.ForeignKey(
        'clubs.Club',
        on_delete=models.CASCADE,
        related_name='substitutions'
    )
    player_out = models.ForeignKey(
        'players.Player',
        on_delete=models.CASCADE,
        related_name='substitutions_out'
    )
    player_in = models.ForeignKey(
        'players.Player',
        on_delete=models.CASCADE,
        related_name='substitutions_in'
    )
    minute = models.PositiveIntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['minute', 'id']

    def clean(self):
        super().clean()
        if not self.match_id:
            return
        valid_clubs = {self.match.home_team_id, self.match.away_team_id}
        if self.team_id and self.team_id not in valid_clubs:
            raise ValidationError('This substitution cannot be recorded for a club not in this match.')
        if self.player_out_id and self.player_out.club_id not in valid_clubs:
            raise ValidationError('The player going out does not belong to either club in this match.')
        if self.player_in_id and self.player_in.club_id not in valid_clubs:
            raise ValidationError('The player coming in does not belong to either club in this match.')
        if self.team_id and self.player_out_id and self.player_out.club_id != self.team_id:
            raise ValidationError('The player going out must belong to the substituted team.')
        if self.team_id and self.player_in_id and self.player_in.club_id != self.team_id:
            raise ValidationError('The player coming in must belong to the substituted team.')

    def __str__(self):
        return f"{self.player_out} -> {self.player_in} ({self.team.name})"
