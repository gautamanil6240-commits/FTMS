"""Tests for matches/services.py: round-robin, groups, and knockout brackets."""
from itertools import combinations

from django.test import TestCase

from clubs.models import Club
from ftms_test_helpers import make_user, make_club, make_tournament, make_approved_registration
from matches.models import Match
from matches.services import (
    distribute_groups,
    generate_group_fixtures,
    generate_round_robin_fixtures,
    generate_knockout_bracket,
    _generate_bracket_from_clubs,
    build_bracket_data,
)
from organizer.models import TournamentRegistration


class RoundRobinTests(TestCase):
    def setUp(self):
        self.organizer = make_user('rr_organizer', 'organizer')
        self.tournament = make_tournament(self.organizer, 'League Cup')
        self.clubs = []
        for i in range(4):
            manager = make_user(f'rr_mgr_{i}', 'manager')
            club = make_club(f'RR Club {i}', manager)
            make_approved_registration(self.tournament, club, manager)
            self.clubs.append(club)

    def test_generates_exactly_one_fixture_per_pair(self):
        created = generate_round_robin_fixtures(self.tournament)
        expected = len(list(combinations(self.clubs, 2)))
        self.assertEqual(len(created), expected)  # 4 clubs -> 6 matches

    def test_every_club_plays_every_other_club(self):
        generate_round_robin_fixtures(self.tournament)
        for home, away in combinations(self.clubs, 2):
            self.assertTrue(
                Match.objects.filter(
                    tournament=self.tournament, home_team=home, away_team=away
                ).exists()
            )

    def test_regenerating_does_not_duplicate_fixtures(self):
        first = generate_round_robin_fixtures(self.tournament)
        second = generate_round_robin_fixtures(self.tournament)
        self.assertEqual(len(second), 0)
        self.assertEqual(Match.objects.filter(tournament=self.tournament).count(), len(first))

    def test_no_club_plays_itself(self):
        generate_round_robin_fixtures(self.tournament)
        for match in Match.objects.filter(tournament=self.tournament):
            self.assertNotEqual(match.home_team_id, match.away_team_id)

    def test_fewer_than_two_approved_clubs_creates_nothing(self):
        solo_tournament = make_tournament(self.organizer, 'Solo Cup')
        manager = make_user('rr_solo_mgr', 'manager')
        make_approved_registration(solo_tournament, make_club('RR Solo FC', manager), manager)
        self.assertEqual(generate_round_robin_fixtures(solo_tournament), [])
        self.assertFalse(Match.objects.filter(tournament=solo_tournament).exists())

    def test_rejected_clubs_are_excluded(self):
        manager = make_user('rr_rej_mgr', 'manager')
        rejected = make_club('RR Rejected FC', manager)
        TournamentRegistration.objects.create(
            tournament=self.tournament, club=rejected,
            status='rejected', registered_by=manager,
        )
        generate_round_robin_fixtures(self.tournament)
        played_clubs = set()
        for m in Match.objects.filter(tournament=self.tournament):
            played_clubs.update([m.home_team_id, m.away_team_id])
        self.assertNotIn(rejected.id, played_clubs)


class GroupDistributionTests(TestCase):
    def setUp(self):
        self.organizer = make_user('grp_organizer', 'organizer')
        self.tournament = make_tournament(self.organizer, 'Group Cup')
        self.registrations = []
        for i in range(6):
            manager = make_user(f'grp_mgr_{i}', 'manager')
            club = make_club(f'GRP Club {i}', manager)
            self.registrations.append(
                make_approved_registration(self.tournament, club, manager)
            )

    def test_even_distribution_across_groups(self):
        distribute_groups(self.tournament, group_count=2, advancers_per_group=2)
        labels = [r.group_label for r in TournamentRegistration.objects.filter(tournament=self.tournament)]
        self.assertEqual(labels.count('A'), 3)
        self.assertEqual(labels.count('B'), 3)

    def test_group_fixtures_only_pair_same_group(self):
        distribute_groups(self.tournament, group_count=2, advancers_per_group=2)
        created = generate_group_fixtures(self.tournament, 'A')
        group_a_clubs = set(
            TournamentRegistration.objects.filter(
                tournament=self.tournament, status='approved', group_label='A'
            ).values_list('club_id', flat=True)
        )
        self.assertEqual(len(created), 3)  # 3 clubs -> 3 pairings
        for match in created:
            self.assertIn(match.home_team_id, group_a_clubs)
            self.assertIn(match.away_team_id, group_a_clubs)


class KnockoutBracketTests(TestCase):
    def _bracket(self, team_count):
        organizer = make_user(f'ko_org_{team_count}', 'organizer')
        tournament = make_tournament(organizer, f'KO Cup {team_count}', fmt='knockout')
        clubs = []
        for i in range(team_count):
            manager = make_user(f'ko_mgr_{team_count}_{i}', 'manager')
            club = make_club(f'KO {team_count} Club {i}', manager)
            make_approved_registration(tournament, club, manager)
            clubs.append(club)
        return tournament, clubs, generate_knockout_bracket(tournament)

    def _assert_bracket_invariants(self, tournament, clubs, matches, expected_rounds):
        self.assertEqual(
            Match.objects.filter(tournament=tournament).count(), len(matches)
        )
        finals = [m for m in matches if m.round_number == expected_rounds]
        self.assertEqual(len(finals), 1)

        # Every team appears exactly once in round 1 or round 2 (byes)
        r1_teams, r2_teams = [], []
        for m in matches:
            if m.round_number == 1:
                self.assertIsNotNone(m.home_team)
                self.assertIsNotNone(m.away_team)
                r1_teams += [m.home_team_id, m.away_team_id]
            elif m.round_number == 2:
                r2_teams += [t.id for t in (m.home_team, m.away_team) if t]
        all_first_round = r1_teams + r2_teams
        self.assertEqual(sorted(all_first_round), sorted(c.id for c in clubs))

        # Wiring: every non-final match points at its parent and no match
        # plays itself once filled.
        final = finals[0]
        for m in matches:
            if m.pk != final.pk:
                self.assertIsNotNone(m.next_match)
            if m.home_team_id and m.away_team_id:
                self.assertNotEqual(m.home_team_id, m.away_team_id)

    def test_power_of_two_bracket_8_teams(self):
        tournament, clubs, matches = self._bracket(8)
        # 8 teams: 4+2+1 = 7 matches, 3 rounds, no byes
        self.assertEqual(len(matches), 7)
        self.assertEqual(max(m.round_number for m in matches), 3)
        self._assert_bracket_invariants(tournament, clubs, matches, 3)

    def test_bracket_with_byes_6_teams(self):
        tournament, clubs, matches = self._bracket(6)
        # bracket_size=8, byes=2: 2 non-bye teams -> 1 live R1 match, whose
        # winner joins the 2 bye teams in R2. Ghost R1 slots are removed.
        self.assertEqual(max(m.round_number for m in matches), 3)
        self._assert_bracket_invariants(tournament, clubs, matches, 3)
        self.assertEqual(len([m for m in matches if m.round_number == 1]), 2)

    def test_minimum_two_teams(self):
        """Regression: a 2-team bracket previously produced zero matches
        (r2_count==0 meant the pairing passes never assigned the finalists).
        The final must exist with both teams assigned."""
        tournament, clubs, matches = self._bracket(2)
        self.assertEqual(len(matches), 1)  # just the final
        final = matches[0]
        self.assertEqual(final.round_number, 1)
        self.assertIsNotNone(final.home_team)
        self.assertIsNotNone(final.away_team)
        self.assertIsNone(final.next_match)

    def test_bracket_from_explicit_clubs_matches_main_algorithm(self):
        organizer = make_user('ko_explicit_org', 'organizer')
        tournament = make_tournament(organizer, 'KO Explicit Cup', fmt='knockout')
        clubs = []
        for i in range(5):
            manager = make_user(f'ko_ex_mgr_{i}', 'manager')
            club = make_club(f'KOEX Club {i}', manager)
            make_approved_registration(tournament, club, manager)
            clubs.append(club)
        matches = _generate_bracket_from_clubs(tournament, clubs)
        self._assert_bracket_invariants(tournament, clubs, matches, 3)


class BracketDataTests(TestCase):
    def test_build_bracket_data_labels_and_winner_side(self):
        organizer = make_user('bd_organizer', 'organizer')
        tournament = make_tournament(organizer, 'BD Cup', fmt='knockout')
        clubs = []
        for i in range(2):
            manager = make_user(f'bd_mgr_{i}', 'manager')
            club = make_club(f'BD Club {i}', manager)
            make_approved_registration(tournament, club, manager)
            clubs.append(club)
        (final,) = generate_knockout_bracket(tournament)
        final.home_team, final.away_team = clubs[0], clubs[1]
        final.home_score, final.away_score = 2, 1
        final.status = 'completed'
        final.save()

        data = build_bracket_data(tournament)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['label'], 'Final')
        entry = data[0]['matches'][0]
        self.assertEqual(entry['winner_side'], 'home')
        self.assertEqual(entry['home_name'], clubs[0].name)

    def test_empty_tournament_builds_no_bracket_data(self):
        organizer = make_user('bd_empty_org', 'organizer')
        tournament = make_tournament(organizer, 'BD Empty Cup', fmt='knockout')
        self.assertEqual(build_bracket_data(tournament), [])
