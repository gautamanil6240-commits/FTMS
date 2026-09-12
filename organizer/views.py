from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.db.models import Case, When, Value, IntegerField
from accounts.models import UserProfile
from clubs.models import get_or_create_manager_club
from .models import Tournament, TournamentRegistration
from .forms import TournamentForm
from matches.services import distribute_groups, generate_group_fixtures, generate_knockout_bracket
from matches.models import Match
from notifications.services import notify, get_club_coach_users

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

    upcoming_matches = Match.objects.filter(
        tournament__organizer=request.user
    ).exclude(status__in=['completed', 'cancelled']).select_related(
        'tournament', 'home_team', 'away_team'
    ).annotate(
        has_date=Case(
            When(match_date__isnull=True, then=Value(1)),
            default=Value(0),
            output_field=IntegerField(),
        )
    ).order_by('has_date', 'match_date')[:5]

    recent_results = Match.objects.filter(
        tournament__organizer=request.user,
        status='completed'
    ).select_related(
        'tournament', 'home_team', 'away_team'
    ).order_by('-match_date', '-id')[:3]

    context = {
        'tournaments': tournaments,
        'total': tournaments.count(),
        'active': tournaments.filter(status='active').count(),
        'registration': tournaments.filter(status='registration').count(),
        'completed': tournaments.filter(status='completed').count(),
        'pending_registrations': pending_registrations,
        'upcoming_matches': upcoming_matches,
        'recent_results': recent_results,
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
# EDIT TOURNAMENT
# =========================

@login_required
def edit_tournament(request, pk):
    if not is_organizer(request.user):
        messages.error(request, 'Access denied!')
        return redirect('login_selection')

    # Ownership is enforced by the organizer filter in the lookup itself.
    tournament = get_object_or_404(Tournament, pk=pk, organizer=request.user)

    if request.method == 'POST':
        form = TournamentForm(request.POST, request.FILES, instance=tournament)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tournament updated successfully!')
            return redirect('organizer_tournament_detail', pk=tournament.pk)
    else:
        form = TournamentForm(instance=tournament)

    return render(request, 'organizer/edit_tournament.html', {
        'form': form,
        'tournament': tournament,
    })


# =========================
# DELETE TOURNAMENT
# =========================

@login_required
def delete_tournament(request, pk):
    if not is_organizer(request.user):
        messages.error(request, 'Access denied!')
        return redirect('login_selection')

    tournament = get_object_or_404(Tournament, pk=pk, organizer=request.user)

    # Eligibility is recomputed on every request (GET and POST alike) so a
    # schedule generated in another tab while the confirm page is open can
    # never slip through — same TOCTOU shape as the approval race fix.
    can_delete = (
        tournament.status in ('registration', 'upcoming')
        and not Match.objects.filter(tournament=tournament).exists()
    )

    if request.method == 'POST':
        if not can_delete:
            messages.error(
                request,
                'This tournament already has a schedule or has started and cannot be deleted.'
            )
            return redirect('organizer_tournament_detail', pk=tournament.pk)

        tournament.delete()
        messages.success(request, f'"{tournament.name}" has been deleted.')
        return redirect('organizer_dashboard')

    return render(request, 'organizer/delete_tournament_confirm.html', {
        'tournament': tournament,
        'can_delete': can_delete,
    })


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
    comments = tournament.comments.select_related('author').all()

    return render(
        request,
        'organizer/tournament_detail.html',
        {'tournament': tournament, 'comments': comments}
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
        with transaction.atomic():
            tournament = Tournament.objects.select_for_update().get(
                pk=registration.tournament_id
            )

            approved_count = TournamentRegistration.objects.filter(
                tournament=tournament,
                status='approved'
            ).count()

            if approved_count >= tournament.max_teams:
                messages.error(
                    request,
                    f'Cannot approve: "{tournament.name}" is already full '
                    f'({approved_count}/{tournament.max_teams}).'
                )
                return redirect('approve_registrations')

            registration.status = 'approved'
            registration.reviewed_by = request.user
            registration.reviewed_at = timezone.now()
            registration.save()

        notify(
            registration.registered_by,
            f'Your registration for {registration.club.name} in "{tournament.name}" was approved.',
            link=f'/tournament/{tournament.pk}/'
        )

        # Notify all coaches of the approved club
        for coach_user in get_club_coach_users(registration.club):
            notify(
                coach_user,
                f"Your club's registration for \"{tournament.name}\" was approved.",
                link=f'/tournament/{tournament.pk}/'
            )

        messages.success(request, f'Approved {registration.club.name} for {registration.tournament.name}.')
        return redirect('approve_registrations')

    elif action == 'reject':
        registration.status = 'rejected'

        notify(
            registration.registered_by,
            f'Your registration for {registration.club.name} in "{registration.tournament.name}" was rejected.',
            link=f'/tournament/{registration.tournament.pk}/'
        )

        messages.success(request, f'Rejected {registration.club.name} for {registration.tournament.name}.')
    else:
        messages.error(request, 'Invalid action.')
        return redirect('approve_registrations')

    registration.reviewed_by = request.user
    registration.reviewed_at = timezone.now()
    registration.save()

    return redirect('approve_registrations')


# =========================
# GROUP DISTRIBUTION (group_ko format)
# =========================

@login_required
def distribute_groups_view(request, tournament_pk):
    """Organizer distributes approved clubs into groups."""
    if not is_organizer(request.user):
        messages.error(request, 'Access denied!')
        return redirect('login_selection')

    tournament = get_object_or_404(Tournament, pk=tournament_pk, organizer=request.user)

    if tournament.format != 'group_ko':
        messages.error(request, 'Group distribution is only available for Group + Knockout tournaments.')
        return redirect('organizer_tournament_detail', pk=tournament.pk)

    approved_count = tournament.registrations.filter(status='approved').count()
    if approved_count < 2:
        messages.error(request, 'At least 2 approved teams are required.')
        return redirect('organizer_tournament_detail', pk=tournament.pk)

    already_distributed = tournament.registrations.filter(
        status='approved', group_label__gt=''
    ).exists()

    if request.method == 'POST':
        if already_distributed:
            messages.error(request, 'Groups are already distributed. Reset first to re-distribute.')
            return redirect('organizer_tournament_detail', pk=tournament.pk)

        try:
            group_count = int(request.POST.get('group_count', 2))
            advancers = int(request.POST.get('advancers_per_group', 1))
        except (ValueError, TypeError):
            messages.error(request, 'Invalid group count or advancers value.')
            return redirect('organizer:distribute_groups', tournament_pk=tournament.pk)

        if group_count < 2 or group_count > approved_count:
            messages.error(request, f'Group count must be between 2 and {approved_count}.')
            return redirect('organizer:distribute_groups', tournament_pk=tournament.pk)

        if advancers < 1:
            messages.error(request, 'At least 1 team must advance per group.')
            return redirect('organizer:distribute_groups', tournament_pk=tournament.pk)

        total_advancing = group_count * advancers
        if total_advancing > approved_count:
            messages.error(
                request,
                f'{group_count} groups × {advancers} advancers = {total_advancing} teams, '
                f'but only {approved_count} are registered. Reduce groups or advancers.'
            )
            return redirect('organizer:distribute_groups', tournament_pk=tournament.pk)

        distribute_groups(tournament, group_count, advancers)
        messages.success(
            request,
            f'Distributed {approved_count} clubs into {group_count} groups ({advancers} advancers each).'
        )
        return redirect('organizer_tournament_detail', pk=tournament.pk)

    registrations = tournament.registrations.filter(
        status='approved'
    ).select_related('club').order_by('club__name')

    context = {
        'tournament': tournament,
        'registrations': registrations,
        'already_distributed': already_distributed,
    }
    return render(request, 'organizer/distribute_groups.html', context)


@login_required
def generate_group_schedule(request, tournament_pk):
    """Generate round-robin fixtures for all groups."""
    if not is_organizer(request.user):
        messages.error(request, 'Access denied!')
        return redirect('login_selection')

    tournament = get_object_or_404(Tournament, pk=tournament_pk, organizer=request.user)

    if tournament.format != 'group_ko':
        messages.error(request, 'This action is only for Group + Knockout tournaments.')
        return redirect('organizer_tournament_detail', pk=tournament.pk)

    from matches.models import Match
    groups = tournament.registrations.filter(
        status='approved', group_label__gt=''
    ).values_list('group_label', flat=True).distinct()

    if not groups:
        messages.error(request, 'Distribute clubs into groups first.')
        return redirect('organizer:distribute_groups', tournament_pk=tournament.pk)

    if Match.objects.filter(tournament=tournament).exists():
        messages.error(request, 'Matches already exist. Delete them before regenerating.')
        return redirect('organizer_tournament_detail', pk=tournament.pk)

    if request.method == 'POST':
        total_created = 0
        for label in sorted(set(groups)):
            created = generate_group_fixtures(tournament, label)
            total_created += len(created)

        messages.success(
            request,
            f'Generated {total_created} group matches across {len(set(groups))} groups.'
        )
        return redirect('matches:schedule', tournament_pk=tournament.pk)

    group_sizes = {}
    for label in sorted(set(groups)):
        group_sizes[label] = tournament.registrations.filter(
            status='approved', group_label=label
        ).count()

    context = {
        'tournament': tournament,
        'groups': sorted(set(groups)),
        'group_sizes': group_sizes,
    }
    return render(request, 'organizer/generate_group_schedule.html', context)


@login_required
def generate_bracket_from_groups(request, tournament_pk):
    """Generate knockout bracket from group stage advancers."""
    if not is_organizer(request.user):
        messages.error(request, 'Access denied!')
        return redirect('login_selection')

    tournament = get_object_or_404(Tournament, pk=tournament_pk, organizer=request.user)

    if tournament.format != 'group_ko':
        messages.error(request, 'This action is only for Group + Knockout tournaments.')
        return redirect('organizer_tournament_detail', pk=tournament.pk)

    from matches.models import Match
    from standings.services import get_tournament_standings

    group_matches = Match.objects.filter(tournament=tournament, round_number=1)
    incomplete = group_matches.exclude(status='completed').count()
    if incomplete:
        messages.error(
            request,
            f'{incomplete} group match(es) are still incomplete. '
            f'Finish all group results before generating the bracket.'
        )
        return redirect('matches:schedule', tournament_pk=tournament.pk)

    if Match.objects.filter(tournament=tournament).exclude(round_number=1).exists():
        messages.error(request, 'Bracket already exists for this tournament.')
        return redirect('matches:bracket_view', tournament_pk=tournament.pk)

    from organizer.models import TournamentRegistration
    groups = tournament.registrations.filter(
        status='approved', group_label__gt=''
    ).values_list('group_label', flat=True).distinct()

    advancing_clubs = []
    for label in sorted(set(groups)):
        group_regs = TournamentRegistration.objects.filter(
            tournament=tournament,
            status='approved',
            group_label=label,
        ).select_related('club')
        advancers_count = group_regs.first().advancers if group_regs else 1

        group_standings = get_tournament_standings(tournament, group_label=label)
        top_n = group_standings[:advancers_count]
        for row in top_n:
            advancing_clubs.append(row['club'])

    if len(advancing_clubs) < 2:
        messages.error(request, 'Not enough advancing teams to form a bracket (need at least 2).')
        return redirect('organizer_tournament_detail', pk=tournament.pk)

    if request.method == 'POST':
        from matches.services import _generate_bracket_from_clubs
        created = _generate_bracket_from_clubs(tournament, advancing_clubs)
        messages.success(
            request,
            f'Knockout bracket generated: {len(created)} matches from {len(advancing_clubs)} advancing teams.'
        )
        return redirect('matches:bracket_view', tournament_pk=tournament.pk)

    advancing_info = []
    for label in sorted(set(groups)):
        group_regs = TournamentRegistration.objects.filter(
            tournament=tournament,
            status='approved',
            group_label=label,
        ).select_related('club')
        advancers_count = group_regs.first().advancers if group_regs else 1
        group_standings = get_tournament_standings(tournament, group_label=label)
        top_n = group_standings[:advancers_count]
        advancing_info.append({
            'group': label,
            'advancers_count': advancers_count,
            'teams': [row['club'] for row in top_n],
        })

    context = {
        'tournament': tournament,
        'advancing_info': advancing_info,
        'total_advancing': len(advancing_clubs),
    }
    return render(request, 'organizer/generate_bracket_from_groups.html', context)
