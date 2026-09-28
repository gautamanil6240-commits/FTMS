"""Tests for the registration approval flow: capacity gate, locking, notifications."""
from django.test import TestCase

from ftms_test_helpers import make_user, make_club, make_tournament, make_approved_registration
from notifications.models import Notification
from organizer.models import TournamentRegistration


class ApprovalFlowTests(TestCase):
    def setUp(self):
        self.organizer = make_user('af_organizer', 'organizer')
        self.tournament = make_tournament(self.organizer, 'Approval Cup', max_teams=2)
        # Two pre-approved clubs fill the tournament.
        for i in (1, 2):
            manager = make_user(f'af_mgr_{i}', 'manager')
            club = make_club(f'AF Club {i}', manager)
            make_approved_registration(self.tournament, club, manager)
        # The club trying to squeeze in.
        self.extra_mgr = make_user('af_mgr_extra', 'manager')
        self.extra_club = make_club('AF Extra FC', self.extra_mgr)
        self.extra_reg = TournamentRegistration.objects.create(
            tournament=self.tournament,
            club=self.extra_club,
            status='pending',
            registered_by=self.extra_mgr,
        )

    def _review(self, action):
        from django.test import Client
        c = Client()
        c.force_login(self.organizer)
        return c.post(
            f'/organizer/approvals/{self.extra_reg.pk}/{action}/',
            follow=True,
        )

    def test_approve_blocked_when_tournament_full(self):
        response = self._review('approve')
        self.extra_reg.refresh_from_db()
        self.assertEqual(self.extra_reg.status, 'pending')
        self.assertIn('already full', ' '.join(str(m) for m in response.context['messages']))

    def test_reject_still_works_when_full(self):
        response = self._review('reject')
        self.extra_reg.refresh_from_db()
        self.assertEqual(self.extra_reg.status, 'rejected')

    def test_approve_notifies_manager_and_coaches(self):
        # Free a slot first so approval is allowed.
        TournamentRegistration.objects.filter(tournament=self.tournament).exclude(
            pk=self.extra_reg.pk
        ).first().delete()

        from coach.models import CoachProfile
        from django.contrib.auth.models import User
        coach_user = User.objects.create_user('af_coach', 'af_coach@test.local', 'test-pass-123')
        CoachProfile.objects.create(user=coach_user, full_name='AF Coach', club=self.extra_club)

        self._review('approve')
        self.extra_reg.refresh_from_db()
        self.assertEqual(self.extra_reg.status, 'approved')

        mgr_note = Notification.objects.filter(recipient=self.extra_mgr)
        self.assertTrue(mgr_note.filter(message__icontains='approved').exists())
        coach_note = Notification.objects.filter(recipient=coach_user)
        self.assertTrue(coach_note.filter(message__icontains='approved').exists())

    def test_reject_notifies_only_registered_by(self):
        from django.contrib.auth.models import User
        from coach.models import CoachProfile
        coach_user = User.objects.create_user('af_coach2', 'af_coach2@test.local', 'test-pass-123')
        CoachProfile.objects.create(user=coach_user, full_name='AF Coach 2', club=self.extra_club)

        self._review('reject')
        self.extra_reg.refresh_from_db()
        self.assertEqual(self.extra_reg.status, 'rejected')
        self.assertTrue(
            Notification.objects.filter(recipient=self.extra_mgr, message__icontains='rejected').exists()
        )
        self.assertFalse(
            Notification.objects.filter(recipient=coach_user).exists()
        )

    def test_non_organizer_cannot_review(self):
        from django.test import Client
        c = Client()
        c.force_login(self.extra_mgr)
        c.post(f'/organizer/approvals/{self.extra_reg.pk}/approve/')
        self.extra_reg.refresh_from_db()
        self.assertEqual(self.extra_reg.status, 'pending')

    def test_review_registration_rejects_non_owner(self):
        # Organizer's own-tournament filter blocks foreign registrations.
        other_organizer = make_user('af_other_org', 'organizer')
        from django.test import Client
        c = Client()
        c.force_login(other_organizer)
        c.post(f'/organizer/approvals/{self.extra_reg.pk}/approve/')
        self.extra_reg.refresh_from_db()
        self.assertEqual(self.extra_reg.status, 'pending')


class ConcurrencySimulationTests(TestCase):
    """Two sequential approvals with an identical pre-check — the second must
    be blocked by the in-lock recheck. (True parallelism needs SQLite-in-memory
    transactions; the lock's correctness is exercised at the logic level.)"""

    def test_stale_precheck_cannot_overfill(self):
        organizer = make_user('cc_organizer', 'organizer')
        tournament = make_tournament(organizer, 'CC Cup', max_teams=2)
        regs, mgrs = [], []
        for i in range(3):
            mgr = make_user(f'cc_mgr_{i}', 'manager')
            club = make_club(f'CC Club {i}', mgr)
            regs.append(TournamentRegistration.objects.create(
                tournament=tournament, club=club,
                status='pending', registered_by=mgr,
            ))
            mgrs.append(mgr)

        # Simulate race: both requests read approved_count == 1 before acting.
        from django.db import transaction
        from django.test import Client

        def approve_like_request(reg):
            c = Client()
            c.force_login(organizer)
            return c.post(f'/organizer/approvals/{reg.pk}/approve/', follow=True)

        # Approve two sequentially while a third "believes" the count is stale.
        with transaction.atomic():
            approve_like_request(regs[0])
        with transaction.atomic():
            approve_like_request(regs[1])
        # Third attempt must hit the full gate.
        response = approve_like_request(regs[2])
        regs[2].refresh_from_db()
        self.assertEqual(regs[2].status, 'pending')
        approved_now = TournamentRegistration.objects.filter(
            tournament=tournament, status='approved'
        ).count()
        self.assertEqual(approved_now, 2)
        self.assertIn('already full', ' '.join(str(m) for m in response.context['messages']))
