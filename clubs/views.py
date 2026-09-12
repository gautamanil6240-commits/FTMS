from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Case, IntegerField, Q, Value, When
from .models import Club, Coach, get_or_create_manager_club
from accounts.models import UserProfile
from coach.models import CoachProfile, get_club_active_lineup
from players.models import Player
from organizer.models import TournamentRegistration
from matches.models import Match
from standings.services import get_club_standing

User = get_user_model()

# =======================================================
# 1. CLUB MANAGER REGISTRATION VIEW
# =======================================================
class ClubManagerRegisterView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('clubs:manager_dashboard')
        return render(request, 'clubs/register_manager.html')

    def post(self, request):
        club_name = request.POST.get('club_name')
        city = request.POST.get('club_city')
        username = request.POST.get('username')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        # Files
        logo = request.FILES.get('club_logo')
        pan_doc = request.FILES.get('pan_document')
        govt_doc = request.FILES.get('government_document')
        cit_doc = request.FILES.get('citizenship_document')

        # Validation Checks
        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return redirect('clubs:register_manager')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username is already taken.")
            return redirect('clubs:register_manager')

        if Club.objects.filter(name=club_name).exists():
            messages.error(request, "A club with this name is already registered.")
            return redirect('clubs:register_manager')

        try:
            # Create User Account
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1
            )

            # Create Associated Club Profile
            Club.objects.create(
                manager=user,
                name=club_name,
                city=city,
                phone=phone,
                logo=logo,
                pan_document=pan_doc,
                government_document=govt_doc,
                citizenship_document=cit_doc
            )

            # Create UserProfile for login compatibility
            UserProfile.objects.create(
                user=user,
                role='manager',
                phone_number=phone or '',
                is_verified=True,
                club_name=club_name,
                club_address=city or '',
            )

            # Log the user in directly after successful sign-up
            login(request, user)
            messages.success(request, "Club registration submitted successfully! Welcome to your manager dashboard.")
            return redirect('clubs:manager_dashboard')

        except Exception as e:
            messages.error(request, f"Registration failed due to an error: {str(e)}")
            return redirect('clubs:register_manager')


# =======================================================
# 2. CLUB MANAGER DASHBOARD
# =======================================================
class ClubManagerDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'clubs/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            # Auto-create the Club record if it is missing (covers legacy
            # accounts registered before Club linkage was added).
            club = get_or_create_manager_club(self.request.user)
            if club is None:
                raise Club.DoesNotExist
            context['club'] = club
            context['coaches'] = club.club_coaches.all()
            context['has_club'] = True
# Real squad roster from players.Player, most recent 5 first
            context['recent_players'] = Player.objects.filter(
                club=club
            ).order_by('-created_at')[:5]

            # Upcoming fixtures where the club is home or away, excluding
            # completed/cancelled matches, soonest first (dated fixtures before
            # TBD ones), capped at 5 like recent_players.
            context['upcoming_matches'] = Match.objects.filter(
                Q(home_team=club) | Q(away_team=club)
            ).exclude(status__in=['completed', 'cancelled']).order_by(
                Case(When(match_date__isnull=True, then=Value(1)), default=Value(0), output_field=IntegerField()),
                'match_date'
            )[:5]

            # Club standings: this club's own position in every tournament it
            # is approved for — scoped to "your club only".
            approved_regs = TournamentRegistration.objects.filter(
                club=club,
                status='approved'
            ).select_related('tournament')
            context['club_standings'] = [
                s for s in (
                    get_club_standing(club, reg.tournament) for reg in approved_regs
                ) if s is not None
            ]

            # Read-only tactics: the club's active formation + slots.
            # Shared helper returns (formation, slots); club derived from
            # request.user.managed_club (never from a URL param).
            formation, lineup_slots = get_club_active_lineup(club)
            context['formation'] = formation
            context['lineup_slots'] = lineup_slots
        except (Club.DoesNotExist, AttributeError):
            context['has_club'] = False
            context['recent_players'] = []
            context['upcoming_matches'] = []
            context['club_standings'] = []
            context['formation'] = None
            context['lineup_slots'] = []
        return context


# =======================================================
# 3. COACH LOOKUP (AJAX)
# =======================================================

@login_required
def coach_lookup(request):
    """Return JSON with coach info for a given coach_id_number.

    Used by the add-coach form for live auto-fill: the manager types a
    Coach ID and the form fetches the coach's name, email, and phone so
    they can confirm before assigning.
    """
    coach_id = request.GET.get('coach_id_number', '').strip()
    profile = UserProfile.objects.filter(
        coach_id_number=coach_id, role='coach'
    ).select_related('user').first()

    if not profile:
        return JsonResponse({'found': False})
    if profile.assigned_manager_id is not None:
        return JsonResponse({'found': False, 'error': 'This coach is already assigned to another club.'})

    return JsonResponse({
        'found': True,
        'full_name': f'{profile.user.first_name} {profile.user.last_name}'.strip(),
        'email': profile.user.email,
        'phone': profile.phone_number or '',
    })


# =======================================================
# 4. ADD COACH VIEW (claim instead of create)
# =======================================================

class AddCoachView(LoginRequiredMixin, View):
    def _get_club_or_redirect(self, request):
        """Return (club, response). If club is missing, response is a redirect."""
        club = get_or_create_manager_club(request.user)
        if club is None:
            messages.error(request, "No club is associated with your manager account. Please contact support.")
            return None, redirect('clubs:manager_dashboard')
        return club, None

    def get(self, request):
        club, response = self._get_club_or_redirect(request)
        if response is not None:
            return response

        return render(request, 'clubs/add_coach.html', {
            'club': club,
            'coaches': club.club_coaches.all(),
        })

    def post(self, request):
        club, response = self._get_club_or_redirect(request)
        if response is not None:
            return response

        coach_id_number = request.POST.get('coach_id_number', '').strip()

        context = {
            'club': club,
            'coaches': club.club_coaches.all(),
        }

        if not coach_id_number:
            messages.error(request, "Please enter a Coach ID.")
            return render(request, 'clubs/add_coach.html', context)

        # Look up the coach by their auto-generated ID (COACH-XXXXXX format)
        profile = UserProfile.objects.filter(
            coach_id_number=coach_id_number, role='coach'
        ).select_related('user').first()

        if not profile:
            messages.error(request, "No coach found with that ID. Make sure the coach has registered first.")
            return render(request, 'clubs/add_coach.html', context)

        if profile.assigned_manager_id is not None:
            messages.error(request, "This coach is already assigned to another club.")
            return render(request, 'clubs/add_coach.html', context)

        coach_user = profile.user
        full_name = f'{coach_user.first_name} {coach_user.last_name}'.strip()

        try:
            # Link the UserProfile to this manager
            profile.assigned_manager = request.user
            profile.save(update_fields=['assigned_manager'])

            # Create CoachProfile (for coach app login compatibility)
            CoachProfile.objects.get_or_create(
                user=coach_user,
                defaults={
                    'club': club,
                    'coach_id_number': coach_id_number,
                    'full_name': full_name,
                    'phone_number': profile.phone_number or '',
                },
            )

            # Create clubs.Coach record (for manager dashboard compatibility)
            Coach.objects.get_or_create(
                user=coach_user,
                defaults={
                    'club': club,
                    'full_name': full_name,
                    'coach_id_number': coach_id_number,
                    'email': coach_user.email,
                    'phone': profile.phone_number or '',
                },
            )

            messages.success(
                request,
                f"✅ Coach {full_name} ({coach_id_number}) has been added to your staff!"
            )
            return redirect('clubs:add_coach')

        except Exception as e:
            messages.error(request, f"Error assigning coach: {e}")
            return render(request, 'clubs/add_coach.html', context)


# =======================================================
# 4. MY CLUB'S TOURNAMENT REGISTRATIONS
# =======================================================

class ClubRegistrationsView(LoginRequiredMixin, TemplateView):
    template_name = 'clubs/my_registrations.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        club = get_or_create_manager_club(self.request.user)
        if club is None:
            context['has_club'] = False
            context['registrations'] = []
            return context

        context['has_club'] = True
        context['club'] = club
        context['registrations'] = TournamentRegistration.objects.filter(
            club=club
        ).select_related('tournament').order_by('-registered_at')
        return context
