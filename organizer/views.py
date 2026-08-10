from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from accounts.models import UserProfile
from clubs.models import get_or_create_manager_club
from .models import Tournament, TournamentRegistration
from .forms import TournamentForm

# SECURITY HELPER 
def is_organizer(user):
    """Checks if the user has the 'organizer' role."""
    try:
        return user.userprofile.role == 'organizer'
    except UserProfile.DoesNotExist:
        return False


def is_manager(user):
    """Checks if the user has the 'manager' role."""
    try:
        return user.userprofile.role == 'manager'
    except UserProfile.DoesNotExist:
        return False

# =========================
# DASHBOARD
# =========================

@login_required
def organizer_dashboard(request):
    if not is_organizer(request.user):
        messages.error(request, 'Access denied!')
        return redirect('login_selection')

    tournaments = Tournament.objects.filter(organizer=request.user)

    pending_registrations = TournamentRegistration.objects.filter(
        tournament__organizer=request.user,
        status='pending'
    ).count()

    context = {
        'tournaments': tournaments,
        'total': tournaments.count(),
        'active': tournaments.filter(status='active').count(),
        'registration': tournaments.filter(status='registration').count(),
        'completed': tournaments.filter(status='completed').count(),
        'pending_registrations': pending_registrations,
    }

    return render(request, 'organizer/organizer_dashboard.html', context)


# =========================
# CREATE TOURNAMENT
# =========================

@login_required
def create_tournament(request):
    if not is_organizer(request.user):
        messages.error(request, 'Access denied!')
        return redirect('login_selection')

    if request.method == 'POST':
        form = TournamentForm(request.POST, request.FILES)
        if form.is_valid():
            tournament = form.save(commit=False)
            tournament.organizer = request.user
            tournament.save()
            messages.success(request, 'Tournament created successfully!')
            return redirect('organizer_dashboard')
    else:
        form = TournamentForm()

    return render(request, 'organizer/create_tournament.html', {'form': form})


# =========================
# PUBLIC TOURNAMENT LIST
# =========================

def tournament_list(request):
    tournaments = Tournament.objects.all().order_by('-created_at')

    status_filter = request.GET.get('status', 'all')

    if status_filter in ('upcoming', 'active', 'registration', 'completed'):
        tournaments = tournaments.filter(status=status_filter)

    return render(
        request,
        'organizer/tournament_list.html',
        {
            'tournaments': tournaments,
            'status_filter': status_filter,
        }
    )


# =========================
# PUBLIC TOURNAMENT DETAIL
# =========================

def tournament_detail(request, pk):
    tournament = get_object_or_404(Tournament, pk=pk)

    return render(
        request,
        'organizer/tournament_detail.html',
        {'tournament': tournament}
    )


# =========================
# CLUB REGISTRATION FOR A TOURNAMENT
# =========================

@login_required
def register_club_for_tournament(request, tournament_pk):
    if not is_manager(request.user):
        messages.error(request, 'Access denied! Only club managers can register for tournaments.')
        return redirect('login_selection')

    # Resolve the manager's club (reuse helper in case Club row is missing)
    club = get_or_create_manager_club(request.user)
    if club is None:
        messages.error(request, 'No club is associated with your manager account. Please contact support.')
        return redirect('clubs:manager_dashboard')

    tournament = get_object_or_404(Tournament, pk=tournament_pk)

    # Friendly duplicate check before trusting the UniqueConstraint
    already = TournamentRegistration.objects.filter(
        tournament=tournament,
        club=club
    ).exists()
    already_status = None
    if already:
        already_status = TournamentRegistration.objects.get(
            tournament=tournament,
            club=club
        ).status

    if request.method == 'POST':
        if already:
            messages.error(request, 'Your club has already registered for this tournament.')
            return redirect('organizer_register_tournament', tournament_pk=tournament.pk)

        if tournament.teams_count >= tournament.max_teams:
            messages.error(request, 'This tournament is already full. No more registrations are accepted.')
            return redirect('organizer_register_tournament', tournament_pk=tournament.pk)

        TournamentRegistration.objects.create(
            tournament=tournament,
            club=club,
            status='pending',
            registered_by=request.user,
        )
        messages.success(request, 'Your club registration has been submitted for approval!')
        return redirect('clubs:my_registrations')

    context = {
        'tournament': tournament,
        'club': club,
        'already': already,
        'already_status': already_status,
    }
    return render(request, 'organizer/register_tournament.html', context)


# =========================
# ORGANIZER APPROVAL QUEUE
# =========================

@login_required
def approve_registrations(request):
    if not is_organizer(request.user):
        messages.error(request, 'Access denied!')
        return redirect('login_selection')

    registrations = TournamentRegistration.objects.filter(
        tournament__organizer=request.user,
        status='pending'
    ).order_by('-registered_at')

    return render(
        request,
        'organizer/approve_registrations.html',
        {'registrations': registrations}
    )


@login_required
def review_registration(request, registration_pk, action):
    if not is_organizer(request.user):
        messages.error(request, 'Access denied!')
        return redirect('login_selection')

    registration = get_object_or_404(
        TournamentRegistration,
        pk=registration_pk,
        tournament__organizer=request.user,
    )

    if action == 'approve':
        # Re-check capacity at approval time (someone else may have filled it)
        if registration.tournament.teams_count >= registration.tournament.max_teams:
            messages.error(
                request,
                f'Cannot approve: "{registration.tournament.name}" is already full '
                f'({registration.tournament.teams_count}/{registration.tournament.max_teams}).'
            )
            return redirect('approve_registrations')

        registration.status = 'approved'
        messages.success(request, f'Approved {registration.club.name} for {registration.tournament.name}.')
    elif action == 'reject':
        registration.status = 'rejected'
        messages.success(request, f'Rejected {registration.club.name} for {registration.tournament.name}.')
    else:
        messages.error(request, 'Invalid action.')
        return redirect('approve_registrations')

    registration.reviewed_by = request.user
    registration.reviewed_at = timezone.now()
    registration.save()

    return redirect('approve_registrations')
