from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.models import UserProfile
from .models import Tournament
from .forms import TournamentForm


@login_required
def organizer_dashboard(request):

    try:
        profile = UserProfile.objects.get(user=request.user)
        if profile.role != 'organizer':
            messages.error(request, 'Access denied!')
            return redirect('login_selection')
    except UserProfile.DoesNotExist:
        return redirect('login_selection')

    tournaments = Tournament.objects.filter(
        organizer=request.user
    )

    context = {
        'tournaments': tournaments,
        'total': tournaments.count(),
        'active': tournaments.filter(status='active').count(),
        'registration': tournaments.filter(status='registration').count(),
        'completed': tournaments.filter(status='completed').count(),
    }

    return render(
        request,
        'organizer/organizer_dashboard.html',
        context
    )


@login_required
def create_tournament(request):

    if request.method == 'POST':

        form = TournamentForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            tournament = form.save(
                commit=False
            )

            tournament.organizer = request.user

            tournament.save()

            messages.success(
                request,
                'Tournament created successfully!'
            )

            return redirect(
                'organizer_dashboard'
            )

    else:

        form = TournamentForm()

    return render(
        request,
        'organizer/create_tournament.html',
        {
            'form': form
        }
    )


@login_required
def organizer_tournament_detail(request, pk):

    tournament = get_object_or_404(
        Tournament,
        pk=pk,
        organizer=request.user
    )

    return render(
        request,
        'organizer/tournament_detail.html',
        {
            'tournament': tournament
        }
    )