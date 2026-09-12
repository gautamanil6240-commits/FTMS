from .models import Notification


def notify(user, message, link=''):
    """Create a notification for a user. Single reusable helper for all trigger points."""
    if user:
        Notification.objects.create(recipient=user, message=message, link=link)


def get_club_coach_users(club):
    """Return the set of User objects for all coaches linked to a club.

    Covers both self-registered coaches (coach.models.CoachProfile) and
    manager-assigned coaches (clubs.models.Coach). Both link directly to
    User, so no fragile email-matching is needed.
    """
    from coach.models import CoachProfile
    from clubs.models import Coach as ClubCoach

    users = set()
    for cp in CoachProfile.objects.filter(club=club).select_related('user'):
        users.add(cp.user)
    for cc in ClubCoach.objects.filter(club=club, user__isnull=False).select_related('user'):
        users.add(cc.user)
    return users
