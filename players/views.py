from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required  # Security check for logged-in users
from .forms import PlayerRawRegistrationForm, PlayerProfileEditForm, PlayerAchievementForm
from .models import Player, PlayerAchievement
from clubs.models import Club  
from accounts.models import UserProfile
from django.shortcuts import get_object_or_404
from coach.models import get_club_active_lineup
from notifications.services import get_club_coach_users, notify

def register(request, role):
    """Processes registration based on the role passed from the URL string."""
    if role == 'player':
        if request.method == 'POST':
            post_data = request.POST.copy()
            
            # Username and password now come directly from the form
            form = PlayerRawRegistrationForm(post_data, request.FILES)

            if form.is_valid():
                # 1. Create basic User account
                user = User.objects.create_user(
                    username=form.cleaned_data['username'],
                    email=form.cleaned_data['email'],
                    password=form.cleaned_data['password']
                )

                # 2. Create UserProfile for login authentication compatibility
                UserProfile.objects.create(
                    user=user,
                    role='player',
                    phone_number=form.cleaned_data['phone'],
                    is_verified=True,
                    date_of_birth=form.cleaned_data['dob'],
                )

                # 3. Create database entry in Player table as a Free Agent
                Player.objects.create(
                    club=None,  # Explicitly set to None
                    full_name=form.cleaned_data['full_name'],
                    profile_photo=form.cleaned_data['profile_photo'],
                    date_of_birth=form.cleaned_data['dob'],
                    gender=form.cleaned_data['gender'].lower(), 
                    nationality=form.cleaned_data['nationality'],
                    phone_number=form.cleaned_data['phone'],
                    email=form.cleaned_data['email'],
                    citizenship_document=form.cleaned_data['id_document'], 
                    preferred_position=form.cleaned_data['position'].lower(), 
                    preferred_jersey_number=form.cleaned_data['jersey_no'] if form.cleaned_data['jersey_no'] else None,
                    height=form.cleaned_data['height'],
                    weight=form.cleaned_data['weight'],
                    medical_status=form.cleaned_data['medical_status'].lower() 
                )

                messages.success(
                    request, 
                    f"Registration successful! Log in using your username ({user.username}) and password."
                )
                return redirect('login') 

            # Return registration form with validation errors if invalid
            return render(request, 'auth/register_player.html', {'errors': form.errors})

        # Render blank registration template on GET request
        return render(request, 'auth/register_player.html')
        
    else:
        messages.info(request, f"Registration for role '{role}' is currently under development.")
        return redirect('login_selection')


@login_required
def player_dashboard(request):
    """Displays dashboard and handles profile updates & achievements."""
    # Try to find the player profile, but handle the case where it might not exist
    try:
        player = Player.objects.get(email=request.user.email)
    except Player.DoesNotExist:
        player = None

    # Determine which form was submitted
    form = PlayerProfileEditForm(instance=player) if player else None
    achievement_form = PlayerAchievementForm()

    if request.method == 'POST' and player:
        if 'add_achievement' in request.POST:
            # Handle achievement submission
            achievement_form = PlayerAchievementForm(request.POST, request.FILES)
            if achievement_form.is_valid():
                achievement = achievement_form.save(commit=False)
                achievement.player = player
                achievement.save()
                messages.success(request, "Achievement added successfully!")
                return redirect('players:player_dashboard')
            else:
                messages.error(request, "Please fix the errors in the achievement form.")
        else:
            # Handle profile edit submission
            form = PlayerProfileEditForm(request.POST, request.FILES, instance=player)
            if form.is_valid():
                form.save()
                messages.success(request, "Your player profile has been updated successfully!")
                return redirect('players:player_dashboard')

    # Fetch achievements for this player
    achievements = player.achievements.all() if player else []

    # Fetch performance records logged by coaches (read-only for players)
    performance_records = player.performance_records.all() if player else []

# Build Chart.js-ready datasets for graphical representation
    performance_chart_data = player.performance_chart_data() if player else None

    # Tactical lineup: the club's active formation + slots (read-only for players)
    formation, lineup_slots = (get_club_active_lineup(player.club) if player else (None, []))

    # Which slot (if any) this player occupies in the active lineup
    my_slot = None
    if player and lineup_slots:
        for s in lineup_slots:
            if s.player_id == player.id:
                my_slot = s
                break

    context = {
        'player': player,
        'form': form,
        'achievement_form': achievement_form,
        'achievements': achievements,
        'performance_records': performance_records,
        'performance_chart_data': performance_chart_data,
        'formation': formation,
        'lineup_slots': lineup_slots,
        'my_slot': my_slot,
    }
    return render(request, 'players/player_dashboard.html', context)

@login_required
def player_list(request):
    """Browse registered players (login required).

    The raw queryset carries contact details and documents, so the template
    only ever receives non-sensitive display fields (name, photo, position,
    age, jersey, club) — never phone/email/citizenship.
    """
    players = Player.objects.select_related('club').order_by('full_name')

    # Only a coach whose profile is linked to a club sees the "Sign" action.
    coach_profile = getattr(request.user, 'coach_profile', None)
    club_coach = getattr(request.user, 'club_coach_profile', None)
    my_club = coach_profile.club if coach_profile else (club_coach.club if club_coach else None)

    return render(request, 'players/player_list.html', {
        'players': players,
        'my_club': my_club,
    })

@login_required
def sign_player(request, player_id):
    """Assigns a free agent player to the logged-in coach's club.

    POST-only (state change must not happen on GET) and coach-only:
    non-coach sessions are rejected before touching the roster.
    """
    if request.method != 'POST':
        messages.error(request, "Invalid request method.")
        return redirect('players:player_list')

    # Role check FIRST — self-registered (coach_profile) and manager-assigned
    # (club_coach_profile) coaches both count; everyone else is rejected
    # before we even reveal whether the player exists.
    coach_profile = getattr(request.user, 'coach_profile', None)
    club_coach = getattr(request.user, 'club_coach_profile', None)
    my_club = coach_profile.club if coach_profile else (club_coach.club if club_coach else None)

    if my_club is None:
        messages.error(request, "Only coaches assigned to a club can sign players.")
        return redirect('players:player_list')

    player = get_object_or_404(Player, player_id=player_id)

    # Free agents only — never poach a player who is under contract elsewhere.
    if player.club_id:
        if player.club_id == my_club.id:
            messages.info(request, f"{player.full_name} is already in your roster.")
        else:
            messages.error(
                request,
                f"{player.full_name} is registered with {player.club.name} and cannot be signed.",
            )
        return redirect('players:player_list')
    
    player.club = my_club
    player.save()

    # Notify all coaches of the club about the new signing
    for coach_user in get_club_coach_users(my_club):
        notify(
            coach_user,
            f'{player.full_name} has been added to the roster.',
            link='/coach/dashboard/'
        )

    # Notify the club manager about the new signing
    if my_club.manager:
        notify(
            my_club.manager,
            f'{player.full_name} has been added to the roster.',
            link='/clubs/dashboard/'
        )

    messages.success(request, f"{player.full_name} has been added to your roster!")
    return redirect('players:player_list')