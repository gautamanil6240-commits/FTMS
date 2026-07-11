from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required  # Security check for logged-in users
from .forms import PlayerRawRegistrationForm, PlayerProfileEditForm
from .models import Player  
from clubs.models import Club  
from django.shortcuts import get_object_or_404

def register(request, role):
    """Processes registration based on the role passed from the URL string."""
    if role == 'player':
        if request.method == 'POST':
            post_data = request.POST.copy()
            
            # Map credentials
            email_input = request.POST.get('email', '')
            post_data['username'] = email_input
            
            phone_input = request.POST.get('phone', '')
            post_data['password'] = phone_input

            form = PlayerRawRegistrationForm(post_data, request.FILES)

            if form.is_valid():
                # 1. Create basic User account
                user = User.objects.create_user(
                    username=form.cleaned_data['username'],
                    email=form.cleaned_data['email'],
                    password=form.cleaned_data['password']
                )

                # 2. Create database entry in Player table as a Free Agent
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
                    f"Registration successful! Log in using your email ({user.email}) as your username."
                )
                return redirect('login') 

            # Return registration form with validation errors if invalid
            return render(request, 'auth/register_player.html', {'errors': form.errors})

        # Render blank registration template on GET request
        return render(request, 'auth/register_player.html')
        
    else:
        messages.info(request, f"Registration for role '{role}' is currently under development.")
        return redirect('login_selection')


@login_required  # Stops unauthenticated users from viewing this dashboard
def player_dashboard(request):
    """Displays the custom dashboard panel once a player logs in successfully."""
    try:
        # Fetches the registered profile details matching the current logged-in user's email address
        player = Player.objects.get(email=request.user.email)
    except Player.DoesNotExist:
        player = None

    context = {
        'player': player,
    }
    return render(request, 'players/player_dashboard.html', context)


def player_list(request):
    """Fetches all registered players from the database and lists them."""
    players = Player.objects.all()
    return render(request, 'players/player_list.html', {'players': players})

@login_required
def player_dashboard(request):
    """Displays dashboard and handles profile updates."""
    # Try to find the player profile, but handle the case where it might not exist
    try:
        player = Player.objects.get(email=request.user.email)
    except Player.DoesNotExist:
        player = None

    # Handle the Edit Profile form submission
    if request.method == 'POST' and player:
        form = PlayerProfileEditForm(request.POST, request.FILES, instance=player)
        if form.is_valid():
            form.save()
            messages.success(request, "Your player profile has been updated successfully!")
            return redirect('players:player_dashboard')
    else:
        form = PlayerProfileEditForm(instance=player) if player else None

    context = {
        'player': player,
        'form': form,
    }
    return render(request, 'players/player_dashboard.html', context)

def player_list(request):
    """Fetches all registered players."""
    players = Player.objects.all()
    return render(request, 'players/player_list.html', {'players': players})

@login_required
def sign_player(request, player_id):
    """Assigns a free agent player to the logged-in coach's club."""
    player = get_object_or_404(Player, player_id=player_id)
    
    # Access the coach profile (adjust 'coachprofile' if your related_name is different)
    try:
        coach = request.user.coachprofile 
        if coach.club:
            player.club = coach.club
            player.save()
            messages.success(request, f"{player.full_name} has been added to your roster!")
        else:
            messages.error(request, "Your coach profile is not linked to any club.")
    except AttributeError:
        messages.error(request, "You do not have a coach profile.")
        
    return redirect('coach:coach_dashboard')