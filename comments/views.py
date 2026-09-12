from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect

from accounts.models import UserProfile
from matches.models import Match
from organizer.models import Tournament

from .models import Comment


def _is_viewer(user):
    """Return True if the user has a viewer profile."""
    try:
        return user.userprofile.role == 'viewer'
    except UserProfile.DoesNotExist:
        return False


@login_required
def add_tournament_comment(request, tournament_pk):
    if request.method != 'POST':
        return redirect('tournament_detail', pk=tournament_pk)

    tournament = get_object_or_404(Tournament, pk=tournament_pk)

    if not _is_viewer(request.user):
        messages.warning(request, "Only viewer accounts can comment.")
        return redirect('tournament_detail', pk=tournament_pk)

    text = request.POST.get('text', '').strip()
    if not text:
        messages.error(request, "Comment cannot be empty.")
        return redirect('tournament_detail', pk=tournament_pk)

    Comment.objects.create(
        author=request.user,
        tournament=tournament,
        text=text,
    )
    messages.success(request, "Comment posted.")
    return redirect('tournament_detail', pk=tournament_pk)


@login_required
def add_match_comment(request, match_pk):
    if request.method != 'POST':
        return redirect('matches:match_detail', pk=match_pk)

    match = get_object_or_404(Match, pk=match_pk)

    if not _is_viewer(request.user):
        messages.warning(request, "Only viewer accounts can comment.")
        return redirect('matches:match_detail', pk=match_pk)

    text = request.POST.get('text', '').strip()
    if not text:
        messages.error(request, "Comment cannot be empty.")
        return redirect('matches:match_detail', pk=match_pk)

    Comment.objects.create(
        author=request.user,
        match=match,
        text=text,
    )
    messages.success(request, "Comment posted.")
    return redirect('matches:match_detail', pk=match_pk)
