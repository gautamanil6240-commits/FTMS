import math
from itertools import combinations


def distribute_groups(tournament, group_count, advancers_per_group):
    """Distribute approved clubs evenly across groups.

    Sets group_label and advancers on each TournamentRegistration.
    Returns the list of updated registrations.
    """
    from organizer.models import TournamentRegistration

    registrations = list(
        TournamentRegistration.objects.filter(
            tournament=tournament,
            status='approved',
        ).select_related('club').order_by('club__name')
    )

    if not registrations:
        return []

    labels = [chr(ord('A') + i) for i in range(group_count)]

    for idx, reg in enumerate(registrations):
        reg.group_label = labels[idx % group_count]
        reg.advancers = advancers_per_group

    TournamentRegistration.objects.bulk_update(
        registrations, ['group_label', 'advancers']
    )

    return registrations


def generate_group_fixtures(tournament, group_label):
    """Generate round-robin fixtures for a single group.

    Only creates matches between clubs in the same group.
    Returns the list of created matches.
    """
    from clubs.models import Club
    from organizer.models import TournamentRegistration
    from .models import Match

    group_club_ids = list(
        TournamentRegistration.objects.filter(
            tournament=tournament,
            status='approved',
            group_label=group_label,
        ).values_list('club_id', flat=True)
    )

    if len(group_club_ids) < 2:
        return []

    clubs = list(Club.objects.filter(pk__in=group_club_ids).order_by('name'))

    created_matches = []
    for home_team, away_team in combinations(clubs, 2):
        match, created = Match.objects.get_or_create(
            tournament=tournament,
            home_team=home_team,
            away_team=away_team,
            defaults={
                'status': 'scheduled',
                'match_date': None,
                'round_number': 1,
            },
        )
        if created:
            created_matches.append(match)

    return created_matches


def generate_round_robin_fixtures(tournament):
    """Create league fixtures for all approved clubs in a tournament."""
    from clubs.models import Club
    from .models import Match

    approved_clubs = list(
        Club.objects.filter(
            tournament_registrations__tournament=tournament,
            tournament_registrations__status='approved',
        ).distinct().order_by('name')
    )

    if len(approved_clubs) < 2:
        return []

    created_matches = []
    for home_team, away_team in combinations(approved_clubs, 2):
        match, created = Match.objects.get_or_create(
            tournament=tournament,
            home_team=home_team,
            away_team=away_team,
            defaults={'status': 'scheduled', 'match_date': None},
        )
        if created:
            created_matches.append(match)

    return created_matches


def generate_knockout_bracket(tournament):
    """Create a single-elimination bracket for the tournament.

    Returns a list of all Match objects created.

    Bracket sizing:
        * bracket_size = next power of 2 >= team count.
        * byes = bracket_size - team_count  (first N teams get byes).
        * Bye teams skip Round 1 and are placed directly into Round 2.

    Wiring:
        * Each non-final match has next_match / next_match_slot set so the
          winner flows into the correct slot of the next round.
        * All rounds except Round 1 are created as empty placeholders
          (home_team=None, away_team=None) and filled progressively as
          results come in.
    """
    from clubs.models import Club
    from .models import Match

    # --- 1. Approved clubs (same pattern as league) ---
    approved_clubs = list(
        Club.objects.filter(
            tournament_registrations__tournament=tournament,
            tournament_registrations__status='approved',
        ).distinct().order_by('name')
    )

    team_count = len(approved_clubs)
    if team_count < 2:
        return []

    # --- 2. Bracket sizing ---
    bracket_size = 1 << (team_count - 1).bit_length()  # next power of 2
    byes = bracket_size - team_count
    total_rounds = int(math.log2(bracket_size))

    # First N teams get byes (arbitrary — no seeding data yet)
    bye_teams = approved_clubs[:byes]
    non_bye_teams = approved_clubs[byes:]
    assert len(non_bye_teams) == bracket_size - 2 * byes, \
        f"Non-bye count mismatch: expected {bracket_size - 2 * byes}, got {len(non_bye_teams)}"

    # --- 3. Build all rounds top-down (placeholder rows first) ---
    # rounds[r] = list of Match objects for round r (1-indexed)
    rounds = {}
    for r in range(1, total_rounds + 1):
        matches_in_round = bracket_size // (1 << r)
        rounds[r] = [
            Match(
                tournament=tournament,
                round_number=r,
                status='scheduled',
            )
            for _ in range(matches_in_round)
        ]

    # Bulk-create every round so they have PKs for FK wiring
    all_matches = []
    for r in range(1, total_rounds + 1):
        Match.objects.bulk_create(rounds[r])
        # Re-fetch to get auto-generated PKs
        rounds[r] = list(
            Match.objects.filter(tournament=tournament, round_number=r)
            .order_by('id')
        )
        all_matches.extend(rounds[r])

    # --- 4. Wire next_match / next_match_slot (bottom-up) ---
    # Round r match i  →  Round r+1 match (i // 2)
    # Even i fills 'home', odd i fills 'away'
    for r in range(1, total_rounds):
        for i, match in enumerate(rounds[r]):
            parent = rounds[r + 1][i // 2]
            match.next_match = parent
            match.next_match_slot = 'home' if i % 2 == 0 else 'away'
        # Bulk-update the FK wiring for this round
        Match.objects.bulk_update(
            rounds[r], ['next_match', 'next_match_slot']
        )

    # --- 5. Assign real teams to Round 1 pairings ---
    # Non-bye pairs are spread across R2 home slots first, then away slots,
    # so bye teams land on the opposite side of each R2 match.
    #
    # R1 match i  →  R2 match (i // 2), slot 'home' if i%2==0 else 'away'
    # So pair j filling R1 M(2*j) feeds R2 M(j) home.
    r2_count = bracket_size // 4
    num_pairs = len(non_bye_teams) // 2
    pair_idx = 0

    # First pass: fill R1 matches that feed R2 home slots
    for j in range(r2_count):
        if pair_idx >= num_pairs:
            break
        r1_match = rounds[1][2 * j]
        r1_match.home_team = non_bye_teams[2 * pair_idx]
        r1_match.away_team = non_bye_teams[2 * pair_idx + 1]
        pair_idx += 1

    # Second pass: fill R1 matches that feed R2 away slots
    for j in range(r2_count):
        if pair_idx >= num_pairs:
            break
        r1_match = rounds[1][2 * j + 1]
        r1_match.home_team = non_bye_teams[2 * pair_idx]
        r1_match.away_team = non_bye_teams[2 * pair_idx + 1]
        pair_idx += 1

    # --- 6. Place bye teams directly into Round 2 slots ---
    # Determine which R2 slots are available (not reserved by R1 winners).
    # Bye teams fill available slots in order, spreading across the bracket.
    if total_rounds >= 2:
        available_slots = []
        for j in range(r2_count):
            if rounds[1][2 * j].home_team is None:
                available_slots.append((j, 'home'))
            if rounds[1][2 * j + 1].home_team is None:
                available_slots.append((j, 'away'))

        for idx, team in enumerate(bye_teams):
            if idx < len(available_slots):
                j, slot = available_slots[idx]
                if slot == 'home':
                    rounds[2][j].home_team = team
                else:
                    rounds[2][j].away_team = team

    # --- 7. Clean up ghost Round 1 slots (bye bypassed them entirely) ---
    ghost_matches = [
        m for m in rounds[1]
        if m.home_team_id is None and m.away_team_id is None
    ]
    if ghost_matches:
        ghost_ids = {m.pk for m in ghost_matches}
        Match.objects.filter(pk__in=ghost_ids).delete()
        rounds[1] = [m for m in rounds[1] if m.pk not in ghost_ids]
        all_matches = [m for m in all_matches if m.pk not in ghost_ids]

    # Bulk-update all team assignments
    bulk_update_fields = ['home_team', 'away_team']
    for r in range(1, min(3, total_rounds + 1)):  # only rounds 1 & 2 get teams
        Match.objects.bulk_update(rounds[r], bulk_update_fields)

    return all_matches


def _generate_bracket_from_clubs(tournament, clubs):
    """Create a single-elimination bracket from an explicit list of clubs.

    Same algorithm as generate_knockout_bracket but accepts a pre-determined
    list of advancing teams (used for group+knockout format).
    """
    from .models import Match

    team_count = len(clubs)
    if team_count < 2:
        return []

    bracket_size = 1 << (team_count - 1).bit_length()
    byes = bracket_size - team_count
    total_rounds = int(math.log2(bracket_size))

    bye_teams = clubs[:byes]
    non_bye_teams = clubs[byes:]

    # Build all rounds
    rounds = {}
    for r in range(1, total_rounds + 1):
        matches_in_round = bracket_size // (1 << r)
        rounds[r] = [
            Match(tournament=tournament, round_number=r, status='scheduled')
            for _ in range(matches_in_round)
        ]

    all_matches = []
    for r in range(1, total_rounds + 1):
        Match.objects.bulk_create(rounds[r])
        rounds[r] = list(
            Match.objects.filter(tournament=tournament, round_number=r).order_by('id')
        )
        all_matches.extend(rounds[r])

    # Wire next_match / next_match_slot
    for r in range(1, total_rounds):
        for i, match in enumerate(rounds[r]):
            parent = rounds[r + 1][i // 2]
            match.next_match = parent
            match.next_match_slot = 'home' if i % 2 == 0 else 'away'
        Match.objects.bulk_update(rounds[r], ['next_match', 'next_match_slot'])

    # Assign non-bye pairs to R1
    r2_count = bracket_size // 4
    num_pairs = len(non_bye_teams) // 2
    pair_idx = 0

    for j in range(r2_count):
        if pair_idx >= num_pairs:
            break
        r1_match = rounds[1][2 * j]
        r1_match.home_team = non_bye_teams[2 * pair_idx]
        r1_match.away_team = non_bye_teams[2 * pair_idx + 1]
        pair_idx += 1

    for j in range(r2_count):
        if pair_idx >= num_pairs:
            break
        r1_match = rounds[1][2 * j + 1]
        r1_match.home_team = non_bye_teams[2 * pair_idx]
        r1_match.away_team = non_bye_teams[2 * pair_idx + 1]
        pair_idx += 1

    # Place bye teams
    if total_rounds >= 2:
        available_slots = []
        for j in range(r2_count):
            if rounds[1][2 * j].home_team is None:
                available_slots.append((j, 'home'))
            if rounds[1][2 * j + 1].home_team is None:
                available_slots.append((j, 'away'))

        for idx, team in enumerate(bye_teams):
            if idx < len(available_slots):
                j, slot = available_slots[idx]
                if slot == 'home':
                    rounds[2][j].home_team = team
                else:
                    rounds[2][j].away_team = team

    # Clean up ghost Round 1 slots (bye bypassed them entirely)
    ghost_matches = [
        m for m in rounds[1]
        if m.home_team_id is None and m.away_team_id is None
    ]
    if ghost_matches:
        ghost_ids = {m.pk for m in ghost_matches}
        Match.objects.filter(pk__in=ghost_ids).delete()
        rounds[1] = [m for m in rounds[1] if m.pk not in ghost_ids]
        all_matches = [m for m in all_matches if m.pk not in ghost_ids]

    bulk_update_fields = ['home_team', 'away_team']
    for r in range(1, min(3, total_rounds + 1)):
        Match.objects.bulk_update(rounds[r], bulk_update_fields)

    return all_matches



def build_bracket_data(tournament):
    """Build a template-ready data structure for the bracket display.

    Returns a list of rounds (dicts), each containing a list of match dicts.
    Rounds are ordered left-to-right: Round 1 first, Final last.
    """
    from .models import Match

    matches = list(
        Match.objects.filter(tournament=tournament)
        .select_related('home_team', 'away_team', 'next_match')
        .order_by('round_number', 'id')
    )

    if not matches:
        return []

    # Group by round
    rounds_map = {}
    for m in matches:
        rounds_map.setdefault(m.round_number, []).append(m)

    total_rounds = max(rounds_map.keys())

    # Round labels
    round_labels = {}
    for r in range(1, total_rounds + 1):
        remaining = total_rounds - r
        if remaining == 0:
            round_labels[r] = 'Final'
        elif remaining == 1:
            round_labels[r] = 'Semi-Final'
        elif remaining == 2:
            round_labels[r] = 'Quarter-Final'
        else:
            round_labels[r] = f'Round {r}'

    bracket_data = []
    for r in range(1, total_rounds + 1):
        round_matches = []
        for m in rounds_map.get(r, []):
            # Determine winner side for completed matches
            winner_side = None
            if m.status == 'completed' and m.home_score is not None and m.away_score is not None:
                if m.home_score > m.away_score:
                    winner_side = 'home'
                elif m.away_score > m.home_score:
                    winner_side = 'away'
                elif m.penalty_home_score is not None and m.penalty_away_score is not None:
                    if m.penalty_home_score > m.penalty_away_score:
                        winner_side = 'home'
                    elif m.penalty_away_score > m.penalty_home_score:
                        winner_side = 'away'

            penalty_text = ''
            if m.penalty_home_score is not None and m.penalty_away_score is not None:
                if m.home_score is not None and m.away_score is not None and m.home_score == m.away_score:
                    penalty_text = f'Pens {m.penalty_home_score}-{m.penalty_away_score}'

            date_text = ''
            if m.match_date:
                date_text = m.match_date.strftime('%b %d, %H:%M')

            round_matches.append({
                'id': m.id,
                'home_name': m.home_team.name if m.home_team else None,
                'away_name': m.away_team.name if m.away_team else None,
                'home_score': m.home_score,
                'away_score': m.away_score,
                'status': m.status,
                'winner_side': winner_side,
                'penalty_text': penalty_text,
                'date_text': date_text,
            })

        bracket_data.append({
            'label': round_labels.get(r, f'Round {r}'),
            'matches': round_matches,
        })

    return bracket_data
