from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.contrib import messages
from .models import Club

# =======================================================
# 1. CLUB MANAGER DASHBOARD VIEW
# =======================================================
class ClubManagerDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'clubs/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        try:
            # Fetch the specific club owned by the logged-in manager
            club = user.managed_club
            context['club'] = club
            context['has_club'] = True
            
            # Count the total players registered under this specific club from DB
            context['total_players'] = club.players.count()
            
            # Fetch recent players added to this club (Limit to top 5)
            context['recent_players'] = club.players.order_by('-id')[:5]
            
            # Dynamic stats fields (Ready to link to your Match tables later)
            context['matches_played'] = 0
            context['wins'] = 0
            context['losses'] = 0
            context['draws'] = 0
            
        except (Club.DoesNotExist, AttributeError):
            # Safety catch: If a user logs in but hasn't created a club row yet
            context['has_club'] = False
            context['club'] = None
            context['total_players'] = 0
            context['recent_players'] = []
            context['matches_played'] = 0
            context['wins'] = 0
            context['losses'] = 0
            context['draws'] = 0
            
        return context


# =======================================================
# 2. ADD PLAYER VIEW (FIXED CLASS WRAPPER)
# =======================================================
class AddPlayerView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'clubs/add_player.html')

    def post(self, request):
        name = request.POST.get('name')
        jersey_number = request.POST.get('jersey_number')
        position = request.POST.get('position')

        # 1. Direct Lookup via Model Filtering to bypass session attribute bugs
        try:
            club = Club.objects.get(manager=request.user)
        except Club.DoesNotExist:
            club = None

        # 2. Safety block if no club entry exists in the DB row matching this user
        if not club:
            messages.error(
                request, 
                f"Management key error: No verified club registry found for the account user: '{request.user.username}'."
            )
            return redirect('clubs:manager_dashboard')

        # 3. Check if jersey number is already taken inside this club
        if club.players.filter(jersey_number=jersey_number).exists():
            messages.error(request, f"Jersey number {jersey_number} is already claimed by another squad member.")
            return render(request, 'clubs/add_player.html')

        # 4. Create and automatically attach the player to the club
        club.players.create(
            name=name,
            jersey_number=jersey_number,
            position=position
        )
        
        messages.success(request, f"Successfully registered {name} into your team roster!")
        return redirect('clubs:manager_dashboard')