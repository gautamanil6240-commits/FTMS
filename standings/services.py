def _ordinal(n):
    """Format an integer as an ordinal string, e.g. 3 -> '3rd'."""
    if 10 <= n % 100 <= 20:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
    return f"{n}{suffix}"


def get_tournament_standings(tournament, group_label=None):
    """
    Build the full league standings table for a tournament from its
    completed matches. Used by the public standings page.

    If group_label is provided, only clubs in that group are included
    (used for group+knockout format).

    Standard 3/1/0 scoring: 3 points for a win, 1 for a draw, 0 for a loss.
    Rows are sorted by points (desc), then goal difference (desc), then
    goals scored (desc) — the usual tiebreaker order. Each row carries a
    'position' where clubs tied on every tiebreaker share the same position
    (1, 1, 3 style), and every row also includes W/D/L, goals, and points.
    """
    from clubs.models import Club
    from matches.models import Match

    # Same approved-club lookup used by generate_round_robin_fixtures.
    club_filter = {
        'tournament_registrations__tournament': tournament,
        'tournament_registrations__status': 'approved',
    }
    if group_label:
        club_filter['tournament_registrations__group_label'] = group_label

    clubs = Club.objects.filter(**club_filter).distinct()

    stats = {
        club.id: {
            'club': club,
            'played': 0,
            'won': 0,
            'drawn': 0,
            'lost': 0,
            'goals_for': 0,
            'goals_against': 0,
            'goal_difference': 0,
            'points': 0,
        }
        for club in clubs
    }

    # Only finished matches count toward the table.
    completed_matches = Match.objects.filter(
        tournament=tournament,
        status='completed',
    )

    for match in completed_matches:
        home = stats.get(match.home_team_id)
        away = stats.get(match.away_team_id)
        if home is None or away is None:
            continue

        home_score = match.home_score or 0
        away_score = match.away_score or 0

        home['played'] += 1
        away['played'] += 1
        home['goals_for'] += home_score
        home['goals_against'] += away_score
        away['goals_for'] += away_score
        away['goals_against'] += home_score

        if home_score > away_score:
            home['won'] += 1
            away['lost'] += 1
        elif home_score < away_score:
            away['won'] += 1
            home['lost'] += 1
        else:
            home['drawn'] += 1
            away['drawn'] += 1

    rows = []
    for stat in stats.values():
        stat['goal_difference'] = stat['goals_for'] - stat['goals_against']
        stat['points'] = stat['won'] * 3 + stat['drawn'] * 1
        rows.append(stat)

    rows.sort(key=lambda s: (-s['points'], -s['goal_difference'], -s['goals_for']))

    # Shared positions: clubs equal on every tiebreaker get the same position.
    position = 0
    previous_key = None
    for index, row in enumerate(rows, start=1):
        key = (row['points'], row['goal_difference'], row['goals_for'])
        if key != previous_key:
            position = index
            previous_key = key
        row['position'] = position

    return rows


def get_tournament_chart_data(tournament):
    """
    Aggregate stats for graphical display on the standings page:
    top scorers, cards by team, goals for/against per team.
    """
    from matches.models import Goal, Card
    from django.db.models import Count, Q

    top_scorers = (
        Goal.objects.filter(match__tournament=tournament)
        .values('player__full_name')
        .annotate(goals=Count('id'))
        .order_by('-goals')[:10]
    )

    cards_by_team = (
        Card.objects.filter(match__tournament=tournament)
        .values('player__club__name', 'card_type')
        .annotate(count=Count('id'))
        .order_by('player__club__name')
    )

    # Goals per team (from completed matches)
    from matches.models import Match
    completed_matches = Match.objects.filter(
        tournament=tournament,
        status='completed',
    )
    team_goals = {}
    for m in completed_matches:
        ht = m.home_team.name
        at = m.away_team.name
        hs = m.home_score or 0
        as_ = m.away_score or 0
        team_goals.setdefault(ht, {'for': 0, 'against': 0})
        team_goals.setdefault(at, {'for': 0, 'against': 0})
        team_goals[ht]['for'] += hs
        team_goals[ht]['against'] += as_
        team_goals[at]['for'] += as_
        team_goals[at]['against'] += hs

    return {
        'top_scorers': list(top_scorers),
        'cards_by_team': list(cards_by_team),
        'team_goals': [{'team': t, 'for': v['for'], 'against': v['against']} for t, v in team_goals.items()],
    }


def get_club_standing(club, tournament):
    """
    Return just this club's row from the tournament standings, including its
    position (e.g. position=3, position_ordinal='3rd'). Used by dashboards to
    show "your club only".

    Returns None if the club is not in the tournament's standings (i.e. not an
    approved participant).
    """
    for row in get_tournament_standings(tournament):
        if row['club'].id == club.id:
            return {
                'tournament': tournament,
                'club': club,
                'position': row['position'],
                'position_ordinal': _ordinal(row['position']),
                'points': row['points'],
                'played': row['played'],
                'won': row['won'],
                'drawn': row['drawn'],
                'lost': row['lost'],
                'goals_for': row['goals_for'],
                'goals_against': row['goals_against'],
                'goal_difference': row['goal_difference'],
            }
    return None
