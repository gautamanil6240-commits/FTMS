"""Shared test helpers: user/role/club/tournament factories used by all apps."""
from datetime import date, timedelta

from django.contrib.auth.models import User

from accounts.models import UserProfile
from clubs.models import Club
from organizer.models import Tournament, TournamentRegistration


def make_user(username, role):
    """Create a User + UserProfile with the given role."""
    user = User.objects.create_user(username, f'{username}@test.local', 'test-pass-123')
    UserProfile.objects.create(user=user, role=role)
    return user


def make_club(name, manager):
    """Create a Club managed by the given user."""
    return Club.objects.create(manager=manager, name=name, city='Testville')


def make_tournament(organizer, name, max_teams=8, fmt='league'):
    """Create a Tournament with sensible defaults for tests."""
    return Tournament.objects.create(
        organizer=organizer,
        name=name,
        location='Testville',
        start_date=date.today() + timedelta(days=1),
        end_date=date.today() + timedelta(days=30),
        format=fmt,
        max_teams=max_teams,
        players_per_team=11,
    )


def make_approved_registration(tournament, club, manager):
    """Approve `club` into `tournament` directly (bypasses the view)."""
    return TournamentRegistration.objects.create(
        tournament=tournament,
        club=club,
        status='approved',
        registered_by=manager,
    )
