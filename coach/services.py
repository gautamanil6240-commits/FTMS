from collections import defaultdict

from django.db import models as django_models

from matches.models import Card, Goal, Match, Substitution
from organizer.models import TournamentRegistration
from .models import PlayerPerformance


def get_missing_performance_logs(club, tournament):
    """Return a list of (player, match, highlights) dicts where the coach
    has not yet logged a PlayerPerformance for a completed match.

    Each entry contains:
      - player: the Player instance
      - match: the Match instance
      - goals: number of goals the player scored in that match
      - cards: number of cards the player received (yellow or red)
      - was_subbed_in: whether the player was substituted in
      - was_subbed_out: whether the player was substituted out
      - minutes_played: estimated minutes (90 by default; adjusted if subbed)
      - match_title: "Home vs Away" label for form pre-fill

    Results are sorted by match date descending, then by player name.
    """
    if club is None or tournament is None:
        return []

    # Only completed matches in this tournament involving the club
    matches = Match.objects.filter(
        tournament=tournament,
        status='completed',
    ).filter(
        django_models.Q(home_team=club) | django_models.Q(away_team=club)
    ).select_related('home_team', 'away_team').order_by('-match_date', '-id')

    # All roster players for this club
    players = list(club.players.all())
    if not players or not matches:
        return []

    player_ids = {p.id for p in players}

    # Fetch all existing performance records for these players in this tournament
    existing = set(
        PlayerPerformance.objects.filter(
            player_id__in=player_ids,
            match__tournament=tournament,
            match__isnull=False,
        ).values_list('player_id', 'match_id')
    )

    # Pre-fetch goals, cards, substitutions for all relevant matches
    match_ids = [m.id for m in matches]

    all_goals = Goal.objects.filter(
        match_id__in=match_ids,
        player_id__in=player_ids,
    ).values_list('match_id', 'player_id')

    all_cards = Card.objects.filter(
        match_id__in=match_ids,
        player_id__in=player_ids,
    ).values_list('match_id', 'player_id')

    all_subs = Substitution.objects.filter(
        match_id__in=match_ids,
    ).filter(
        django_models.Q(player_in_id__in=player_ids) | django_models.Q(player_out_id__in=player_ids)
    ).values_list('match_id', 'player_in_id', 'player_out_id', 'minute')

    # Build lookup: (match_id, player_id) -> goals count
    goal_counts = defaultdict(int)
    for m_id, p_id in all_goals:
        goal_counts[(m_id, p_id)] += 1

    # Build lookup: (match_id, player_id) -> card count
    card_counts = defaultdict(int)
    for m_id, p_id in all_cards:
        card_counts[(m_id, p_id)] += 1

    # Build lookup: (match_id, player_id) -> {'in': bool, 'out': bool, 'in_minute': int, 'out_minute': int}
    sub_info = defaultdict(lambda: {'in': False, 'out': False, 'in_minute': None, 'out_minute': None})
    for m_id, p_in, p_out, minute in all_subs:
        if p_in in player_ids:
            key = (m_id, p_in)
            sub_info[key]['in'] = True
            if minute is not None:
                sub_info[key]['in_minute'] = minute
        if p_out in player_ids:
            key = (m_id, p_out)
            sub_info[key]['out'] = True
            if minute is not None:
                sub_info[key]['out_minute'] = minute

    # Assemble missing logs
    missing = []
    for match in matches:
        for player in players:
            if (player.id, match.id) in existing:
                continue

            key = (match.id, player.id)
            goals = goal_counts.get(key, 0)
            cards = card_counts.get(key, 0)
            sub = sub_info.get(key, {'in': False, 'out': False, 'in_minute': None, 'out_minute': None})

            # Estimate minutes played
            minutes = 90
            if sub['in'] and not sub['out']:
                # Came on as sub, never went off
                minutes = 90 - (sub['in_minute'] or 0) if sub['in_minute'] else 90
            elif sub['out'] and not sub['in']:
                # Started but was subbed off
                minutes = sub['out_minute'] or 90

            missing.append({
                'player': player,
                'match': match,
                'goals': goals,
                'cards': cards,
                'was_subbed_in': sub['in'],
                'was_subbed_out': sub['out'],
                'minutes_played': minutes,
                'match_title': f"{match.home_team.name} vs {match.away_team.name}",
            })

    # Sort by match date descending, then player name
    missing.sort(key=lambda x: (-x['match'].match_date.timestamp() if x['match'].match_date else 0, x['player'].full_name))

    return missing


def get_completed_tournaments_for_coach(club):
    """Return approved tournament registrations where status is 'completed'."""
    if club is None:
        return []
    return list(
        TournamentRegistration.objects.filter(
            club=club,
            status='approved',
            tournament__status='completed',
        ).select_related('tournament')
    )
