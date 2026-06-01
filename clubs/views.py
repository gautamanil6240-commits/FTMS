from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Club

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
            context['recent_players'] = club.players.order_by('-created_at')[:5]
            
            # Dynamic stats fields (Ready to link to your Match tables later)
            context['matches_played'] = 0
            context['wins'] = 0
            context['losses'] = 0
            context['draws'] = 0
            
        except (Club.DoesNotExist, AttributeError):
            # Safety catch: If 'roshan' logs in but hasn't created a club row yet
            context['has_club'] = False
            context['club'] = None
            context['total_players'] = 0
            context['recent_players'] = []
            context['matches_played'] = 0
            context['wins'] = 0
            context['losses'] = 0
            context['draws'] = 0
            
        return context