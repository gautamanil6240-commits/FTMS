from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import PlayerRegistrationForm
from clubs.models import Club  

@login_required
def register_player(request):
    # 🧠 Logic: Every player must belong to a club. 
    # We look up the club managed by the currently logged-in user.
    try:
        user_club = Club.objects.get(manager=request.user)
    except Club.DoesNotExist:
        messages.error(request, "Access Denied: You must be registered as a Club Manager to access player enrollment.")
        return redirect('login') # Fallback if user doesn't own a club node

    if request.method == 'POST':
        # Pass both text data (POST) and media files (FILES) to the form
        form = PlayerRegistrationForm(request.POST, request.FILES)
        
        if form.is_valid():
            # Commit=False holds the transaction open so we can inject the club relation
            player = form.save(commit=False)
            player.club = user_club
            player.save()
            
            messages.success(request, f"Registration initialized successfully for {player.full_name}!")
            return redirect('/clubs/dashboard/')  # Redirects straight to your dashboard url path
        else:
            messages.error(request, "System Validation Fault. Please correct the highlighted errors below.")
    else:
        form = PlayerRegistrationForm()

    # ⚡ CENTRALIZED ROUTING: Points directly to the shared accounts directory structure
    return render(request, 'accounts/register_player.html', {'form': form})

@login_required
def player_dashboard(request):
    # 🧠 Look up the player record tied to this logged-in account
    try:
        # Since your teammate linked Player to Club, we fetch the player row 
        # matching the user's email or full name, or via a profile relation.
        # Assuming email matches user email for the player record:
        player = Player.objects.get(email=request.user.email)
    except Player.DoesNotExist:
        messages.error(request, "Profile Not Found: You do not have an active Player enrollment profile.")
        return redirect('login')

    context = {
        'player': player,
        'club': player.club, # Fetches their current assigned team/club node
    }
    return render(request, 'players/player_dashboard.html', context)