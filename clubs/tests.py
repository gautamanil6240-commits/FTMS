from django.test import Client, TestCase

from ftms_test_helpers import make_club, make_tournament, make_user
from organizer.models import TournamentRegistration


class ManagerDashboardAvailableTournamentsTests(TestCase):
    """The manager dashboard's Available Tournaments section lists open and
    active tournaments with the club's own registration status."""

    def setUp(self):
        self.manager = make_user('dash_mgr', 'manager')
        self.club = make_club('Dash United', self.manager)
        self.organizer = make_user('dash_org', 'organizer')
        self.client = Client()
        self.client.force_login(self.manager)

    def _dashboard(self):
        return self.client.get('/clubs/dashboard/')

    def test_registration_open_tournament_listed(self):
        make_tournament(self.organizer, 'Open Cup')
        response = self._dashboard()
        self.assertContains(response, 'Available Tournaments')
        self.assertContains(response, 'Open Cup')
        # Register action is offered to a club that hasn't registered.
        self.assertContains(response, '📝 Register')

    def test_completed_and_upcoming_tournaments_not_listed(self):
        upcoming = make_tournament(self.organizer, 'Ghost Cup')
        upcoming.status = 'upcoming'
        upcoming.save()
        completed = make_tournament(self.organizer, 'Old Cup')
        completed.status = 'completed'
        completed.save()

        response = self._dashboard()
        self.assertNotContains(response, 'Ghost Cup')
        self.assertNotContains(response, 'Old Cup')

    def test_full_tournament_shows_full_badge_not_register(self):
        full = make_tournament(self.organizer, 'Sardine Cup', max_teams=1)
        TournamentRegistration.objects.create(
            tournament=full,
            club=self.club,
            status='approved',
            registered_by=self.manager,
        )

        response = self._dashboard()
        # Own approved registration shows the Registered badge...
        self.assertContains(response, '✅ Registered')
        # ...and no Register button for a full tournament.
        self.assertNotContains(response, '📝 Register')

    def test_pending_registration_shows_pending_badge(self):
        pending = make_tournament(self.organizer, 'Pending Cup')
        TournamentRegistration.objects.create(
            tournament=pending,
            club=self.club,
            status='pending',
            registered_by=self.manager,
        )

        response = self._dashboard()
        self.assertContains(response, '⏱️ Pending')
        self.assertNotContains(response, '📝 Register')

    def test_shows_team_count(self):
        make_tournament(self.organizer, 'Counter Cup', max_teams=4)
        response = self._dashboard()
        self.assertContains(response, '0/4 teams registered')

    def test_no_tournaments_shows_empty_state(self):
        response = self._dashboard()
        self.assertContains(response, 'No tournaments are open right now')

    def test_anonymous_user_redirected(self):
        Client().get('/clubs/dashboard/')
        response = Client().get('/clubs/dashboard/', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'auth/login.html')
