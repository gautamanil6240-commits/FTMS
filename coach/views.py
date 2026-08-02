import json
import re
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import CoachProfile, PlayerPerformance
from datetime import datetime
from django.contrib.auth.models import User
from players.models import Player
from clubs.models import Club
from accounts.models import UserProfile
from .forms import CoachProfileEditForm, PlayerPerformanceForm

# ==========================================
# REGISTER VIEW
# ==========================================
def register_coach_view(request):
    # Fetch available clubs for selection dropdown
    clubs_list = Club.objects.all().order_by('name')

    if request.method == 'POST':
        # Extract fields
        username          = request.POST.get('username', '').strip()
        email             = request.POST.get('email', '').strip()
        first_name        = request.POST.get('first_name', '').strip()
        last_name         = request.POST.get('last_name', '').strip()
        password          = request.POST.get('password', '')
        confirm_password  = request.POST.get('confirm_password', '')
        phone             = request.POST.get('phone', '').strip()
        dob_str           = request.POST.get('dob', '')
        gender            = request.POST.get('gender', '')
        nationality       = request.POST.get('nationality', '').strip()
        highest_education = request.POST.get('highest_education', '').strip()
        selected_club_id  = request.POST.get('club_id', '').strip()

        # Preserve inputs on error
        context = {
            'clubs': clubs_list,
            'saved_inputs': {
                'username': username, 'email': email,
                'first_name': first_name, 'last_name': last_name,
                'phone': phone, 'dob': dob_str, 'gender': gender,
                'nationality': nationality, 'highest_education': highest_education,
                'club_id': selected_club_id,
            }
        }

        # --- Validation Rules ---
        if not all([username, email, first_name, last_name, password, confirm_password, phone, dob_str]):
            messages.error(request, "Please fill out all required fields.")
            return render(request, 'auth/register_coach.html', context)

        if password != confirm_password:
            messages.error(request, "Passwords do not match. Please verify.")
            return render(request, 'auth/register_coach.html', context)

        if len(password) < 8 or not any(c.isdigit() for c in password):
            messages.error(request, "Password must be at least 8 characters and include a number.")
            return render(request, 'auth/register_coach.html', context)

        if User.objects.filter(username=username).exists():
            messages.error(request, "This username is already taken.")
            return render(request, 'auth/register_coach.html', context)

        if User.objects.filter(email=email).exists():
            messages.error(request, "An account with this email already exists.")
            return render(request, 'auth/register_coach.html', context)

        clean_phone = re.sub(r'\D', '', phone)
        if len(clean_phone) != 10:
            messages.error(request, "Phone number must be exactly 10 digits.")
            return render(request, 'auth/register_coach.html', context)

        try:
            dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
            today = datetime.today().date()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            if age < 18:
                messages.error(request, "Coaches must be at least 18 years old.")
                return render(request, 'auth/register_coach.html', context)
        except ValueError:
            messages.error(request, "Invalid date of birth format.")
            return render(request, 'auth/register_coach.html', context)

        # --- Validate club selection ---
        assigned_club = None
        if selected_club_id and selected_club_id.isdigit():
            try:
                assigned_club = Club.objects.get(id=selected_club_id)
            except Club.DoesNotExist:
                messages.error(request, "Selected club does not exist.")
                return render(request, 'auth/register_coach.html', context)

        # --- Save to Database ---
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
            )
            CoachProfile.objects.create(
                user=user,
                club=assigned_club,
                full_name=f"{first_name} {last_name}",
                phone_number=clean_phone,
                date_of_birth=dob,
                gender=gender,
                nationality=nationality,
                education=highest_education,
                profile_photo=request.FILES.get('profile_photo'),
                coaching_license=request.FILES.get('coach_license') and request.FILES['coach_license'].name or '',
                certificates=request.FILES.get('experience_certificate'),
            )
            # Also create a UserProfile so the coach can login via main login page too
            UserProfile.objects.create(
                user=user,
                role='coach',
                phone_number=clean_phone,
                is_verified=True,
                date_of_birth=dob,
                coach_license=request.FILES.get('coach_license'),
                experience_certificate=request.FILES.get('experience_certificate'),
                citizenship_document=request.FILES.get('citizenship_document'),
            )
            messages.success(request, f"Account created! Please log in, {first_name}.")
            return redirect('coach:login_coach_view')

        except Exception as e:
            messages.error(request, f"Registration failed: {str(e)}")
            return render(request, 'auth/register_coach.html', context)

    return render(request, 'auth/register_coach.html', {'clubs': clubs_list})


# ==========================================
# LOGIN VIEW
# ==========================================
def login_coach_view(request):
    if request.user.is_authenticated:
        return redirect('coach:coach_dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        if not username or not password:
            messages.error(request, "Both username and password are required.")
            return render(request, 'auth/login.html', {'saved_username': username, 'role': 'Coach'})

        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Check for coach_profile (self-registered via coach app)
            if hasattr(user, 'coach_profile'):
                login(request, user)
                messages.success(request, f"Welcome back, {user.first_name}!")
                return redirect('coach:coach_dashboard')
            # Check for club_coach_profile (assigned by manager)
            elif hasattr(user, 'club_coach_profile'):
                login(request, user)
                messages.success(request, f"Welcome back, {user.first_name}!")
                return redirect('coach:coach_dashboard')
            else:
                messages.error(request, "No coach profile found for this account.")
                return render(request, 'auth/login.html', {'saved_username': username, 'role': 'Coach'})
        else:
            messages.error(request, "Invalid username or password.")
            return render(request, 'auth/login.html', {'saved_username': username, 'role': 'Coach'})

    return render(request, 'auth/login.html', {'role': 'Coach'})


# ==========================================
# PLAYER DETAIL VIEW (for coach to view player profile)
# ==========================================
def _resolve_coach_profile(request):
    """Returns the coach profile (CoachProfile) for the current user, or None."""
    return getattr(request.user, 'coach_profile', None)


def _resolve_coach_context(request):
    """Returns (club, coach_instance_for_performance_fk) for the current user.

    Supports both self-registered (coach_profile) and manager-assigned
    (club_coach_profile) coaches. The performance coach FK points to
    CoachProfile, so we only return a value for that FK when it's a real
    CoachProfile instance.
    """
    coach_profile = getattr(request.user, 'coach_profile', None)
    if coach_profile:
        return coach_profile.club, coach_profile

    club_coach = getattr(request.user, 'club_coach_profile', None)
    if club_coach:
        return club_coach.club, None  # club_coach is clubs.Coach, not CoachProfile

    return None, None


@login_required
def player_detail_view(request, player_id):
    """Displays detailed information about a player in the coach's roster."""
    player = get_object_or_404(Player, player_id=player_id)

    my_club, _ = _resolve_coach_context(request)

    # Handle performance logging directly from the player detail page
    if request.method == 'POST' and 'add_performance' in request.POST:
        return _log_performance(request, player)

    # Only allow viewing performance for players in the coach's own club
    if my_club and player.club == my_club:
        performance_records = player.performance_records.all()
    else:
        performance_records = []

    return render(request, 'coach/player_detail.html', {
        'player': player,
        'performance_records': performance_records,
        'performance_form': PlayerPerformanceForm(),
        'performance_chart_data': player.performance_chart_data(),
        'can_manage_performance': bool(my_club and player.club == my_club),
    })

@login_required
def player_detail_by_pk(request, pk):
    """Displays detailed information about a player by auto-increment ID."""
    player = get_object_or_404(Player, pk=pk)

    my_club, _ = _resolve_coach_context(request)

    # Handle performance logging directly from the player detail page
    if request.method == 'POST' and 'add_performance' in request.POST:
        return _log_performance(request, player)

    # Only show performance history for players in the coach's own club
    if my_club and player.club == my_club:
        performance_records = player.performance_records.all()
    else:
        performance_records = []

    return render(request, 'coach/player_detail.html', {
        'player': player,
        'performance_records': performance_records,
        'performance_form': PlayerPerformanceForm(),
        'performance_chart_data': player.performance_chart_data(),
        'can_manage_performance': bool(my_club and player.club == my_club),
    })


def _log_performance(request, player):
    """Shared helper: validate & save a PlayerPerformance record for a roster player."""
    my_club, coach_instance = _resolve_coach_context(request)

    # Server-side check: the player must belong to this coach's own club
    if not my_club or player.club != my_club:
        messages.error(request, "You can only log performance for players in your own squad.")
        return redirect('coach:coach_dashboard')

    form = PlayerPerformanceForm(request.POST)
    if form.is_valid():
        performance = form.save(commit=False)
        performance.player = player
        performance.coach = coach_instance  # None for club_coach users (FK expects CoachProfile)
        performance.save()
        messages.success(request, f"Performance record saved for {player.full_name}!")
    else:
        messages.error(request, "Please fix the errors in the performance form.")

    return redirect('coach:player_detail', player_id=player.player_id)

@login_required
def remove_player_from_roster(request, pk):
    """Removes a player from the coach's club roster (sets club to null)."""
    player = get_object_or_404(Player, pk=pk)
    
    # Verify the player belongs to this coach's club
    coach_profile = getattr(request.user, 'coach_profile', None)
    club_coach = getattr(request.user, 'club_coach_profile', None)
    my_club = coach_profile.club if coach_profile else (club_coach.club if club_coach else None)
    
    if my_club and player.club == my_club:
        player.club = None
        player.save()
        messages.success(request, f"{player.full_name} has been removed from the squad.")
    else:
        messages.error(request, "You can only remove players from your own squad.")
    
    return redirect('coach:coach_dashboard')


# ==========================================
# LOGOUT VIEW
# ==========================================
def logout_coach_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('coach:login_coach_view')


# ==========================================
# COACH DASHBOARD VIEW
# ==========================================
@login_required
def coach_dashboard(request):
    # Support both self-registered (coach_profile) and manager-assigned (club_coach_profile) coaches
    coach_profile = getattr(request.user, 'coach_profile', None)
    club_coach = getattr(request.user, 'club_coach_profile', None)
    
    if coach_profile:
        my_club = coach_profile.club
    elif club_coach:
        my_club = club_coach.club
    else:
        return render(request, 'coach/error.html', {
            'message': "Account logged in, but no Coach Profile found."
        })

    # Handle POST Request
    if request.method == 'POST':
        if 'join_club' in request.POST:
            club_id = request.POST.get('join_club_id', '').strip()
            if club_id and club_id.isdigit():
                try:
                    new_club = Club.objects.get(id=club_id)
                    if coach_profile:
                        coach_profile.club = new_club
                        coach_profile.save()
                    elif club_coach:
                        club_coach.club = new_club
                        club_coach.save()
                    my_club = new_club
                    messages.success(request, f"You have joined {new_club.name} successfully!")
                except Club.DoesNotExist:
                    messages.error(request, "Selected club does not exist.")
            else:
                messages.error(request, "Please select a valid club.")
            return redirect('coach:coach_dashboard')

        if 'add_to_roster' in request.POST:
            selected_player_ids = request.POST.getlist('selected_players')
            if selected_player_ids and my_club:
                Player.objects.filter(id__in=selected_player_ids).update(club=my_club)
                messages.success(request, f"Successfully added {len(selected_player_ids)} player(s)!")
            elif not my_club:
                messages.error(request, "Your account is not assigned to any club yet.")
            return redirect('coach:coach_dashboard')

        if 'add_performance' in request.POST:
            player_id = request.POST.get('performance_player_id', '').strip()
            # Server-side check — never trust the submitted player id blindly
            try:
                target_player = Player.objects.get(id=player_id)
            except (Player.DoesNotExist, ValueError):
                messages.error(request, "Invalid player selected.")
                return redirect('coach:coach_dashboard')

            if my_club and target_player.club == my_club:
                form = PlayerPerformanceForm(request.POST)
                if form.is_valid():
                    performance = form.save(commit=False)
                    performance.player = target_player
                    # Coach FK points to CoachProfile; club_coach (clubs.Coach) users leave it null
                    performance.coach = coach_profile
                    performance.save()
                    messages.success(request, f"Performance record saved for {target_player.full_name}!")
                else:
                    messages.error(request, "Please fix the errors in the performance form.")
            else:
                messages.error(request, "You can only log performance for players in your own squad.")
            return redirect('coach:coach_dashboard')

        else:
            form = CoachProfileEditForm(request.POST, request.FILES, instance=coach_profile)
            if form.is_valid():
                form.save()
                messages.success(request, "Profile updated successfully!")
            return redirect('coach:coach_dashboard')

    # Handle GET Request
    available_players = Player.objects.filter(club__isnull=True)
    my_roster = Player.objects.filter(club=my_club) if my_club else []
    all_clubs = Club.objects.all().order_by('name')

    # Use whichever profile is available for the template context
    display_coach = coach_profile or club_coach

    return render(request, 'coach/coach_dashboard.html', {
        'coach': display_coach,
        'form': CoachProfileEditForm(instance=coach_profile) if coach_profile else None,
        'available_players': available_players,
        'my_roster': my_roster,
        'my_club': my_club,
        'all_clubs': all_clubs,
        'performance_form': PlayerPerformanceForm(),
    })
