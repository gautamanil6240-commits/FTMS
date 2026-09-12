import json
from django.shortcuts import get_object_or_404, render

from organizer.models import Tournament
from .services import get_tournament_standings, get_tournament_chart_data


def tournament_standings(request, tournament_pk):
    """Public standings page — no login required, like tournament_detail."""
    tournament = get_object_or_404(Tournament, pk=tournament_pk)
    standings = get_tournament_standings(tournament)
    chart_data = get_tournament_chart_data(tournament)

    # Build simplified JSON-safe versions for Chart.js
    standings_json = [
        {
            'name': row['club'].name,
            'points': row['points'],
            'goals_for': row['goals_for'],
            'goals_against': row['goals_against'],
            'won': row['won'],
            'drawn': row['drawn'],
            'lost': row['lost'],
        }
        for row in standings
    ]

    return render(request, 'standings/standings.html', {
        'tournament': tournament,
        'standings': standings,
        'chart_data': chart_data,
        'standings_json': json.dumps(standings_json),
    })
