from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Tournament
from .forms import TournamentForm


@login_required
def organizer_dashboard(request):

    tournaments = Tournament.objects.filter(
        organizer=request.user
    )

    context = {
        'total': tournaments.count(),
        'active': tournaments.filter(status='active').count(),
        'registration': tournaments.filter(status='registration').count(),
        'completed': tournaments.filter(status='completed').count(),
        'tournaments': tournaments,
    }

    return render(
        request,
        'organizer/dashboard.html',
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

            tournament = form.save(commit=False)

            tournament.organizer = request.user

            tournament.save()

            messages.success(
                request,
                'Tournament created successfully.'
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