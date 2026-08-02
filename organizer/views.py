from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.models import UserProfile
from .models import Tournament
from .forms import TournamentForm

# SECURITY HELPER 
def is_organizer(user):
    """Checks if the user has the 'organizer' role."""
    try:
        return user.userprofile.role == 'organizer'
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

    context = {
        'tournaments': tournaments,
        'total': tournaments.count(),
        'active': tournaments.filter(status='active').count(),
        'registration': tournaments.filter(status='registration').count(),
        'completed': tournaments.filter(status='completed').count(),
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

    return render(
        request,
        'organizer/tournament_list.html',
        {'tournaments': tournaments}
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