"""Tests for standings/services.py: scoring, tiebreakers, shared positions."""
from django.test import TestCase

from ftms_test_helpers import make_user, make_club, make_tournament, make_approved_registration
from matches.models import Match
from standings.services import get_tournament_standings, get_club_standing


class StandingsTests(TestCase):
    def setUp(self):
        self.organizer = make_user('st_organizer', 'organizer')
        self.tournament = make_tournament(self.organizer, 'Standings Cup')
        self.clubs = []
        for i in range(4):
            manager = make_user(f'st_mgr_{i}', 'manager')
            club = make_club(f'ST Club {i}', manager)
            make_approved_registration(self.tournament, club, manager)
            self.clubs.append(club)

    def _play(self, home, away, hs, as_):
        Match.objects.create(
            tournament=self.tournament,
            home_team=home, away_team=away,
            home_score=hs, away_score=as_,
            status='completed',
        )

    def test_perfect_record(self):
        # Club 0 wins everything, big goal difference
        for i in (1, 2, 3):
            self._play(self.clubs[0], self.clubs[i], 3, 0)
        rows = get_tournament_standings(self.tournament)
        top = rows[0]
        self.assertEqual(top['club'], self.clubs[0])
        self.assertEqual(top['played'], 3)
        self.assertEqual(top['won'], 3)
        self.assertEqual(top['points'], 9)
        self.assertEqual(top['goals_for'], 9)
        self.assertEqual(top['goals_against'], 0)
        self.assertEqual(top['goal_difference'], 9)
        self.assertEqual(top['position'], 1)

    def test_three_one_zero_scoring(self):
        self._play(self.clubs[0], self.clubs[1], 1, 0)   # c0 win
        self._play(self.clubs[2], self.clubs[3], 1, 1)   # draw
        rows = get_tournament_standings(self.tournament)
        by_id = {r['club'].id: r for r in rows}
        self.assertEqual(by_id[self.clubs[0].id]['points'], 3)
        self.assertEqual(by_id[self.clubs[1].id]['points'], 0)
        self.assertEqual(by_id[self.clubs[2].id]['points'], 1)
        self.assertEqual(by_id[self.clubs[3].id]['points'], 1)
        self.assertEqual(by_id[self.clubs[2].id]['drawn'], 1)

    def test_unplayed_matches_do_not_count(self):
        self._play(self.clubs[0], self.clubs[1], 2, 0)
        # scheduled but never completed
        Match.objects.create(tournament=self.tournament, home_team=self.clubs[2],
                             away_team=self.clubs[3], status='scheduled')
        # cancelled results must not count either
        Match.objects.create(tournament=self.tournament, home_team=self.clubs[0],
                             away_team=self.clubs[2], home_score=5, away_score=5,
                             status='cancelled')
        rows = get_tournament_standings(self.tournament)
        by_id = {r['club'].id: r for r in rows}
        self.assertEqual(by_id[self.clubs[2].id]['played'], 0)
        self.assertEqual(by_id[self.clubs[0].id]['points'], 3)

    def test_goal_difference_breaks_points_tie(self):
        # Both clubs win 1-0 once: equal points, decided by GD? Both GD +1.
        # Make GD differ: c0 wins 2-0, c1 wins 1-0 -> both 3 pts, c0 GD +2
        self._play(self.clubs[0], self.clubs[2], 2, 0)
        self._play(self.clubs[1], self.clubs[3], 1, 0)
        rows = get_tournament_standings(self.tournament)
        self.assertEqual(rows[0]['club'], self.clubs[0])
        self.assertEqual(rows[1]['club'], self.clubs[1])

    def test_goals_for_breaks_gd_tie(self):
        # c0 wins 3-2 (GD +1), c1 wins 2-1 (GD +1): same pts, same GD,
        # c0 has more goals_for -> c0 first
        self._play(self.clubs[0], self.clubs[2], 3, 2)
        self._play(self.clubs[1], self.clubs[3], 2, 1)
        rows = get_tournament_standings(self.tournament)
        self.assertEqual(rows[0]['club'], self.clubs[0])
        self.assertEqual(rows[1]['club'], self.clubs[1])

    def test_shared_positions_on_full_tie(self):
        # Identical win and identical scoreline everywhere for c0/c1
        self._play(self.clubs[0], self.clubs[2], 1, 0)
        self._play(self.clubs[1], self.clubs[3], 1, 0)
        rows = get_tournament_standings(self.tournament)
        self.assertEqual(rows[0]['position'], 1)
        self.assertEqual(rows[1]['position'], 1)
        # The untouched clubs share position 3 (1,1,3 style)
        self.assertEqual(rows[2]['position'], 3)
        self.assertEqual(rows[3]['position'], 3)

    def test_null_scores_treated_as_zero(self):
        m = Match.objects.create(
            tournament=self.tournament,
            home_team=self.clubs[0], away_team=self.clubs[1],
            status='completed',
        )
        m.home_score = None
        m.away_score = 2
        m.save(update_fields=['away_score'])
        rows = get_tournament_standings(self.tournament)
        by_id = {r['club'].id: r for r in rows}
        self.assertEqual(by_id[self.clubs[0].id]['goals_for'], 0)
        self.assertEqual(by_id[self.clubs[0].id]['goals_against'], 2)
        self.assertEqual(by_id[self.clubs[1].id]['won'], 1)

    def test_get_club_standing_returns_row_with_ordinal(self):
        self._play(self.clubs[0], self.clubs[1], 1, 0)
        row = get_club_standing(self.clubs[0], self.tournament)
        self.assertEqual(row['position'], 1)
        self.assertEqual(row['position_ordinal'], '1st')
        self.assertEqual(row['points'], 3)
        missing = get_club_standing(self.clubs[3], self.tournament)
        self.assertIsNotNone(missing)  # approved participant, just 0 points

    def test_get_club_standing_none_for_non_participant(self):
        manager = make_user('st_outside_mgr', 'manager')
        outsider = make_club('ST Outsider FC', manager)
        self.assertIsNone(get_club_standing(outsider, self.tournament))
