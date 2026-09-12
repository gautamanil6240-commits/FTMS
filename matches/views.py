from datetime import datetime

from django import forms
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.forms import BaseFormSet, formset_factory
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from clubs.models import Club
from organizer.models import Tournament
from players.models import Player
from .models import Card, Goal, Match, Substitution
from .services import generate_round_robin_fixtures, generate_knockout_bracket, build_bracket_data
from notifications.services import notify, get_club_coach_users

User = get_user_model()


def is_organizer(user):
    try:
        return user.userprofile.role == 'organizer'
    except Exception:
        return False


def _determine_winner(match_obj):
    """Return the winning Club for a completed match, or None.

    For knockout matches with a tied score, penalties decide the winner.
    For league / non-bracket matches, returns None (no auto-fill needed).
    """
    if match_obj.home_score is None or match_obj.away_score is None:
        return None

    if match_obj.home_score > match_obj.away_score:
        return match_obj.home_team
    if match_obj.away_score > match_obj.home_score:
        return match_obj.away_team

    # Tied — only resolve if this is a bracket match (next_match exists)
    # and penalty scores were recorded.
    if match_obj.next_match and match_obj.penalty_home_score is not None and match_obj.penalty_away_score is not None:
        if match_obj.penalty_home_score > match_obj.penalty_away_score:
            return match_obj.home_team
        if match_obj.penalty_away_score > match_obj.penalty_home_score:
            return match_obj.away_team

    return None


class MatchResultForm(forms.ModelForm):
    # Penalty fields are extra (not on Match directly) — handled manually.
    penalty_home_score = forms.IntegerField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={'min': 0, 'class': 'form-control'}),
        label='Penalties (Home)',
    )
    penalty_away_score = forms.IntegerField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={'min': 0, 'class': 'form-control'}),
        label='Penalties (Away)',
    )

    class Meta:
        model = Match
        fields = ['home_score', 'away_score']
        widgets = {
            'home_score': forms.NumberInput(attrs={'min': 0, 'class': 'form-control'}),
            'away_score': forms.NumberInput(attrs={'min': 0, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.match_instance = kwargs.get('instance')
        super().__init__(*args, **kwargs)
        # Pre-populate penalty fields from saved values
        if self.match_instance:
            self.fields['penalty_home_score'].initial = self.match_instance.penalty_home_score
            self.fields['penalty_away_score'].initial = self.match_instance.penalty_away_score

    def clean(self):
        cleaned_data = super().clean()
        home_score = cleaned_data.get('home_score')
        away_score = cleaned_data.get('away_score')
        penalty_home = cleaned_data.get('penalty_home_score')
        penalty_away = cleaned_data.get('penalty_away_score')

        if (home_score is None) ^ (away_score is None):
            raise forms.ValidationError('Please provide both home and away scores.')

        if home_score is not None and home_score < 0:
            raise forms.ValidationError('Scores cannot be negative.')
        if away_score is not None and away_score < 0:
            raise forms.ValidationError('Scores cannot be negative.')

        # Knockout tie-breaking: if scores are tied, penalties are required
        is_knockout = (
            self.match_instance
            and self.match_instance.tournament.format in ('knockout', 'group_ko')
            and self.match_instance.next_match is not None
        )
        if is_knockout and home_score is not None and away_score is not None:
            if home_score == away_score:
                if penalty_home is None or penalty_away is None:
                    raise forms.ValidationError(
                        'This is a knockout match and the score is tied. '
                        'Penalty scores are required to determine the winner.'
                    )
                if penalty_home == penalty_away:
                    raise forms.ValidationError(
                        'Penalty scores are tied. They must differ to determine a winner.'
                    )

        return cleaned_data


class GoalEntryForm(forms.ModelForm):
    class Meta:
        model = Goal
        fields = ['team', 'player', 'minute']
        widgets = {
            'team': forms.Select(attrs={'class': 'form-select'}),
            'player': forms.Select(attrs={'class': 'form-select'}),
            'minute': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 120}),
        }

    def __init__(self, *args, match=None, club=None, **kwargs):
        self.match = match
        self.club = club
        super().__init__(*args, **kwargs)

        if match:
            if club:
                # Team-specific goal row: lock the team to this club and only
                # offer that club's players.
                clubs = Club.objects.filter(pk=club.pk)
                players = Player.objects.filter(club=club)
                self.fields['team'].queryset = clubs
                self.fields['team'].widget = forms.HiddenInput()
                self.fields['team'].initial = club.pk
            else:
                clubs = Club.objects.filter(pk__in=[match.home_team_id, match.away_team_id])
                players = Player.objects.filter(club__in=clubs)
                self.fields['team'].queryset = clubs
            self.fields['player'].queryset = players
        else:
            self.fields['team'].queryset = Club.objects.none()
            self.fields['player'].queryset = Player.objects.none()

        self.fields['minute'].required = False

    def clean(self):
        cleaned_data = super().clean()
        team = cleaned_data.get('team')
        player = cleaned_data.get('player')
        minute = cleaned_data.get('minute')

        if not any([team, player, minute]):
            return cleaned_data

        if self.match and team and team.pk not in [self.match.home_team_id, self.match.away_team_id]:
            raise forms.ValidationError('The credited team must be one of the clubs in this match.')

        if self.match and player and player.club_id not in [self.match.home_team_id, self.match.away_team_id]:
            raise forms.ValidationError('The player does not belong to either club in this match.')

        if team and player and player.club_id != team.pk:
            raise forms.ValidationError('The scorer must belong to the credited team.')

        if minute is not None and minute < 1:
            raise forms.ValidationError('Minute must be at least 1.')

        return cleaned_data


class CardEntryForm(forms.ModelForm):
    class Meta:
        model = Card
        fields = ['player', 'card_type', 'minute']
        widgets = {
            'player': forms.Select(attrs={'class': 'form-select'}),
            'card_type': forms.Select(attrs={'class': 'form-select'}),
            'minute': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 120}),
        }

    def __init__(self, *args, match=None, club=None, **kwargs):
        self.match = match
        self.club = club
        super().__init__(*args, **kwargs)

        if match:
            if club:
                # Team-specific card row: only offer that club's players.
                players = Player.objects.filter(club=club)
            else:
                clubs = Club.objects.filter(pk__in=[match.home_team_id, match.away_team_id])
                players = Player.objects.filter(club__in=clubs)
            self.fields['player'].queryset = players
        else:
            self.fields['player'].queryset = Player.objects.none()

        self.fields['minute'].required = False

    def clean(self):
        cleaned_data = super().clean()
        player = cleaned_data.get('player')
        minute = cleaned_data.get('minute')

        if not any([player, minute, cleaned_data.get('card_type')]):
            return cleaned_data

        if self.match and player and player.club_id not in [self.match.home_team_id, self.match.away_team_id]:
            raise forms.ValidationError('The player does not belong to either club in this match.')

        if minute is not None and minute < 1:
            raise forms.ValidationError('Minute must be at least 1.')

        return cleaned_data


class SubstitutionEntryForm(forms.ModelForm):
    class Meta:
        model = Substitution
        fields = ['team', 'player_out', 'player_in', 'minute']
        widgets = {
            'team': forms.Select(attrs={'class': 'form-select'}),
            'player_out': forms.Select(attrs={'class': 'form-select'}),
            'player_in': forms.Select(attrs={'class': 'form-select'}),
            'minute': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 120}),
        }

    def __init__(self, *args, match=None, club=None, **kwargs):
        self.match = match
        self.club = club
        super().__init__(*args, **kwargs)

        if match:
            if club:
                # Team-specific substitution row: lock the team to this club and
                # only offer that club's players for both in and out.
                clubs = Club.objects.filter(pk=club.pk)
                players = Player.objects.filter(club=club)
                self.fields['team'].queryset = clubs
                self.fields['team'].widget = forms.HiddenInput()
                self.fields['team'].initial = club.pk
            else:
                clubs = Club.objects.filter(pk__in=[match.home_team_id, match.away_team_id])
                players = Player.objects.filter(club__in=clubs)
                self.fields['team'].queryset = clubs
            self.fields['player_out'].queryset = players
            self.fields['player_in'].queryset = players
        else:
            self.fields['team'].queryset = Club.objects.none()
            self.fields['player_out'].queryset = Player.objects.none()
            self.fields['player_in'].queryset = Player.objects.none()

        self.fields['minute'].required = False

    def clean(self):
        cleaned_data = super().clean()
        team = cleaned_data.get('team')
        player_out = cleaned_data.get('player_out')
        player_in = cleaned_data.get('player_in')
        minute = cleaned_data.get('minute')

        if not any([team, player_out, player_in, minute]):
            return cleaned_data

        if self.match and team and team.pk not in [self.match.home_team_id, self.match.away_team_id]:
            raise forms.ValidationError('The substitution team must be one of the clubs in this match.')

        if self.match and player_out and player_out.club_id not in [self.match.home_team_id, self.match.away_team_id]:
            raise forms.ValidationError('The player going out does not belong to either club in this match.')

        if self.match and player_in and player_in.club_id not in [self.match.home_team_id, self.match.away_team_id]:
            raise forms.ValidationError('The player coming in does not belong to either club in this match.')

        if team and player_out and player_out.club_id != team.pk:
            raise forms.ValidationError('The player going out must belong to the substituted team.')

        if team and player_in and player_in.club_id != team.pk:
            raise forms.ValidationError('The player coming in must belong to the substituted team.')

        if player_out and player_in and player_out.pk == player_in.pk:
            raise forms.ValidationError('A player cannot be substituted in for themselves.')

        if minute is not None and minute < 1:
            raise forms.ValidationError('Minute must be at least 1.')

        return cleaned_data


class BaseEventFormSet(BaseFormSet):
    def __init__(self, *args, match=None, club=None, **kwargs):
        self.match = match
        self.club = club
        super().__init__(*args, **kwargs)

    def _construct_form(self, i, **kwargs):
        kwargs['match'] = self.match
        if self.club is not None:
            kwargs['club'] = self.club
        return super()._construct_form(i, **kwargs)


GoalFormSet = formset_factory(GoalEntryForm, extra=3, can_delete=True, formset=BaseEventFormSet)
CardFormSet = formset_factory(CardEntryForm, extra=3, can_delete=True, formset=BaseEventFormSet)
SubstitutionFormSet = formset_factory(SubstitutionEntryForm, extra=3, can_delete=True, formset=BaseEventFormSet)


@login_required
def generate_schedule(request, tournament_pk):
    if not is_organizer(request.user):
        messages.error(request, 'Access denied!')
        return redirect('login_selection')

    tournament = get_object_or_404(Tournament, pk=tournament_pk)
    if tournament.organizer_id != request.user.id:
        messages.error(request, 'You do not own this tournament.')
        return redirect('organizer_dashboard')

    if tournament.status == 'registration':
        messages.error(request, 'Close registration before generating the schedule.')
        return redirect('organizer_tournament_detail', pk=tournament.pk)

    if Match.objects.filter(tournament=tournament).exists():
        messages.error(request, 'A schedule already exists for this tournament. Delete existing matches before regenerating.')
        return redirect('organizer_tournament_detail', pk=tournament.pk)

    approved_count = tournament.registrations.filter(status='approved').count()
    if approved_count < 2:
        messages.error(request, 'At least 2 approved teams are required before generating a schedule.')
        return redirect('organizer_tournament_detail', pk=tournament.pk)

    is_knockout = tournament.format in ('knockout', 'group_ko')
    expected_matches = (
        approved_count * (approved_count - 1) // 2
        if not is_knockout
        else approved_count - 1  # approximate for bracket
    )

    if request.method == 'POST':
        if is_knockout:
            created_matches = generate_knockout_bracket(tournament)
        else:
            created_matches = generate_round_robin_fixtures(tournament)
        messages.success(request, f'Schedule generated successfully: {len(created_matches)} matches created for {tournament.name}.')

        # Notify coaches and managers of all approved clubs
        approved_clubs = Club.objects.filter(
            tournament_registrations__tournament=tournament,
            tournament_registrations__status='approved'
        )
        for club in approved_clubs:
            for coach_user in get_club_coach_users(club):
                notify(
                    coach_user,
                    f'The schedule for "{tournament.name}" has been generated.',
                    link=f'/matches/schedule/{tournament.pk}/'
                )
            notify(
                club.manager,
                f'The schedule for "{tournament.name}" has been generated.',
                link=f'/matches/schedule/{tournament.pk}/'
            )

        return redirect('matches:schedule', tournament_pk=tournament.pk)

    context = {
        'tournament': tournament,
        'approved_count': approved_count,
        'expected_matches': expected_matches,
        'is_knockout': is_knockout,
    }
    return render(request, 'matches/generate_schedule.html', context)


@login_required
def view_edit_schedule(request, tournament_pk):
    if not is_organizer(request.user):
        messages.error(request, 'Access denied!')
        return redirect('login_selection')

    tournament = get_object_or_404(Tournament, pk=tournament_pk)
    if tournament.organizer_id != request.user.id:
        messages.error(request, 'You do not own this tournament.')
        return redirect('organizer_dashboard')

    # Knockout / group_ko tournaments use the bracket view, not the table.
    if tournament.format in ('knockout', 'group_ko'):
        return redirect('matches:bracket_view', tournament_pk=tournament.pk)

    matches = Match.objects.filter(tournament=tournament).select_related('home_team', 'away_team').order_by('id')

    if request.method == 'POST':
        updated = 0
        for match in matches:
            field_name = f'match_{match.pk}_date'
            raw_value = request.POST.get(field_name, '')
            if raw_value == '':
                if match.match_date is not None:
                    match.match_date = None
                    match.save(update_fields=['match_date'])
                    updated += 1
                continue

            try:
                parsed = datetime.strptime(raw_value, '%Y-%m-%dT%H:%M')
                aware_dt = timezone.make_aware(parsed, timezone.get_current_timezone())
            except ValueError:
                messages.error(request, f'Invalid datetime for {match}. Please use a valid date and time.')
                continue

            if match.match_date != aware_dt:
                match.match_date = aware_dt
                match.save(update_fields=['match_date'])
                updated += 1

        if updated:
            messages.success(request, f'Updated {updated} match date(s).')
        else:
            messages.info(request, 'No schedule changes were saved.')
        return redirect('matches:schedule', tournament_pk=tournament.pk)

    context = {'tournament': tournament, 'matches': matches}
    return render(request, 'matches/schedule.html', context)


@login_required
def cancel_match(request, match_pk):
    if not is_organizer(request.user):
        messages.error(request, 'Access denied!')
        return redirect('login_selection')

    match = get_object_or_404(Match, pk=match_pk)
    if match.tournament.organizer_id != request.user.id:
        messages.error(request, 'You do not own this tournament.')
        return redirect('organizer_dashboard')

    # POST-only — never cancel on a GET, same reasoning as delete.
    if request.method != 'POST':
        messages.error(request, 'Invalid request.')
        return redirect('matches:schedule', tournament_pk=match.tournament_id)

    if match.status != 'scheduled':
        messages.error(
            request,
            f'This match is {match.get_status_display().lower()} and cannot be cancelled.'
        )
        return redirect('matches:schedule', tournament_pk=match.tournament_id)

    match.status = 'cancelled'
    match.save(update_fields=['status'])
    messages.success(
        request,
        f'{match.home_team.name} vs {match.away_team.name} has been cancelled.'
    )
    return redirect('matches:schedule', tournament_pk=match.tournament_id)


@login_required
def uncancel_match(request, match_pk):
    if not is_organizer(request.user):
        messages.error(request, 'Access denied!')
        return redirect('login_selection')

    match = get_object_or_404(Match, pk=match_pk)
    if match.tournament.organizer_id != request.user.id:
        messages.error(request, 'You do not own this tournament.')
        return redirect('organizer_dashboard')

    if request.method != 'POST':
        messages.error(request, 'Invalid request.')
        return redirect('matches:schedule', tournament_pk=match.tournament_id)

    if match.status != 'cancelled':
        messages.error(
            request,
            f'Only cancelled matches can be restored to scheduled (this match is {match.get_status_display().lower()}).'
        )
        return redirect('matches:schedule', tournament_pk=match.tournament_id)

    match.status = 'scheduled'
    match.save(update_fields=['status'])
    messages.success(
        request,
        f'{match.home_team.name} vs {match.away_team.name} has been restored to scheduled.'
    )
    return redirect('matches:schedule', tournament_pk=match.tournament_id)


@login_required
def enter_match_result(request, match_pk):
    if not is_organizer(request.user):
        messages.error(request, 'Access denied!')
        return redirect('login_selection')

    match = get_object_or_404(Match, pk=match_pk)
    if match.tournament.organizer_id != request.user.id:
        messages.error(request, 'You do not own this tournament.')
        return redirect('organizer_dashboard')

    # A cancelled match must never receive a score.
    if match.status == 'cancelled':
        messages.error(request, 'A cancelled match cannot receive a result.')
        return redirect('matches:schedule', tournament_pk=match.tournament_id)

    if request.method == 'POST':
        result_form = MatchResultForm(request.POST, instance=match)
        home_goal_formset = GoalFormSet(request.POST, prefix='home_goals', match=match, club=match.home_team)
        away_goal_formset = GoalFormSet(request.POST, prefix='away_goals', match=match, club=match.away_team)
        home_card_formset = CardFormSet(request.POST, prefix='home_cards', match=match, club=match.home_team)
        away_card_formset = CardFormSet(request.POST, prefix='away_cards', match=match, club=match.away_team)
        home_sub_formset = SubstitutionFormSet(request.POST, prefix='home_subs', match=match, club=match.home_team)
        away_sub_formset = SubstitutionFormSet(request.POST, prefix='away_subs', match=match, club=match.away_team)

        if (
            result_form.is_valid()
            and home_goal_formset.is_valid()
            and away_goal_formset.is_valid()
            and home_card_formset.is_valid()
            and away_card_formset.is_valid()
            and home_sub_formset.is_valid()
            and away_sub_formset.is_valid()
        ):
            with transaction.atomic():
                match_obj = result_form.save(commit=False)
                match_obj.status = 'completed'
                # Save penalty scores (extra form fields, not auto-saved)
                match_obj.penalty_home_score = result_form.cleaned_data.get('penalty_home_score')
                match_obj.penalty_away_score = result_form.cleaned_data.get('penalty_away_score')
                match_obj.save()

                Goal.objects.filter(match=match_obj).delete()
                Card.objects.filter(match=match_obj).delete()
                Substitution.objects.filter(match=match_obj).delete()

                for goal_form in list(home_goal_formset.cleaned_data) + list(away_goal_formset.cleaned_data):
                    if goal_form and not goal_form.get('DELETE'):
                        Goal.objects.create(
                            match=match_obj,
                            team=goal_form['team'],
                            player=goal_form['player'],
                            minute=goal_form.get('minute'),
                        )

                for card_form in list(home_card_formset.cleaned_data) + list(away_card_formset.cleaned_data):
                    if card_form and not card_form.get('DELETE'):
                        Card.objects.create(
                            match=match_obj,
                            player=card_form['player'],
                            card_type=card_form['card_type'],
                            minute=card_form.get('minute'),
                        )

                for sub_form in list(home_sub_formset.cleaned_data) + list(away_sub_formset.cleaned_data):
                    if sub_form and not sub_form.get('DELETE'):
                        Substitution.objects.create(
                            match=match_obj,
                            team=sub_form['team'],
                            player_out=sub_form['player_out'],
                            player_in=sub_form['player_in'],
                            minute=sub_form.get('minute'),
                        )

                # --- Phase C: Auto-fill next match with the winner ---
                winner = _determine_winner(match_obj)
                if winner and match_obj.next_match:
                    next_match = match_obj.next_match
                    if match_obj.next_match_slot == 'home':
                        next_match.home_team = winner
                    else:
                        next_match.away_team = winner
                    next_match.save(update_fields=['home_team', 'away_team'])

            score_line = f'{match_obj.home_team.name} {match_obj.home_score} - {match_obj.away_score} {match_obj.away_team.name}'

            notify(
                match_obj.home_team.manager,
                f'Result recorded: {score_line}',
                link=f'/matches/match/{match_obj.pk}/'
            )
            notify(
                match_obj.away_team.manager,
                f'Result recorded: {score_line}',
                link=f'/matches/match/{match_obj.pk}/'
            )

            # Notify all roster players in both teams
            roster_players = Player.objects.filter(
                club__in=[match_obj.home_team, match_obj.away_team]
            ).exclude(email='')
            for p in roster_players:
                p_user = User.objects.filter(email=p.email).first()
                if p_user:
                    notify(
                        p_user,
                        f'Result recorded: {score_line}',
                        link=f'/matches/match/{match_obj.pk}/'
                    )

            # Notify all coaches for both clubs
            for club in (match_obj.home_team, match_obj.away_team):
                for coach_user in get_club_coach_users(club):
                    notify(
                        coach_user,
                        f'Result recorded: {score_line}',
                        link=f'/matches/match/{match_obj.pk}/'
                    )

            messages.success(request, f'Result recorded for {match_obj.home_team.name} vs {match_obj.away_team.name}.')
            return redirect('matches:match_detail', match_pk=match_obj.pk)

    else:
        result_form = MatchResultForm(instance=match)
        home_goal_formset = GoalFormSet(prefix='home_goals', match=match, club=match.home_team)
        away_goal_formset = GoalFormSet(prefix='away_goals', match=match, club=match.away_team)
        home_card_formset = CardFormSet(prefix='home_cards', match=match, club=match.home_team)
        away_card_formset = CardFormSet(prefix='away_cards', match=match, club=match.away_team)
        home_sub_formset = SubstitutionFormSet(prefix='home_subs', match=match, club=match.home_team)
        away_sub_formset = SubstitutionFormSet(prefix='away_subs', match=match, club=match.away_team)

    context = {
        'match': match,
        'form': result_form,
        'home_goal_formset': home_goal_formset,
        'away_goal_formset': away_goal_formset,
        'home_card_formset': home_card_formset,
        'away_card_formset': away_card_formset,
        'home_sub_formset': home_sub_formset,
        'away_sub_formset': away_sub_formset,
    }
    return render(request, 'matches/enter_result.html', context)


def match_detail(request, match_pk):
    match = get_object_or_404(Match, pk=match_pk)
    goals = match.goals.select_related('player', 'team').all()
    cards = match.cards.select_related('player').all()
    substitutions = match.substitutions.select_related('team', 'player_out', 'player_in').all()
    context = {
        'match': match,
        'goals': goals,
        'home_goals': goals.filter(team_id=match.home_team_id),
        'away_goals': goals.filter(team_id=match.away_team_id),
        'home_cards': cards.filter(player__club_id=match.home_team_id),
        'away_cards': cards.filter(player__club_id=match.away_team_id),
        'home_subs': substitutions.filter(team_id=match.home_team_id),
        'away_subs': substitutions.filter(team_id=match.away_team_id),
        'comments': match.comments.select_related('author').all(),
    }
    return render(request, 'matches/match_detail.html', context)


@login_required
def bracket_view(request, tournament_pk):
    """Display the knockout bracket for a tournament."""
    if not is_organizer(request.user):
        messages.error(request, 'Access denied!')
        return redirect('login_selection')

    tournament = get_object_or_404(Tournament, pk=tournament_pk)
    if tournament.organizer_id != request.user.id:
        messages.error(request, 'You do not own this tournament.')
        return redirect('organizer_dashboard')

    bracket_data = build_bracket_data(tournament)

    return render(request, 'matches/bracket.html', {
        'tournament': tournament,
        'bracket_data': bracket_data,
    })
