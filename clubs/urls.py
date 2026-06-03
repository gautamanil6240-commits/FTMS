from django.urls import path
from . import views

# This namespace ensures Django knows these URLs belong specifically to the clubs app
app_name = 'clubs'

urlpatterns = [
    # Maps 'localhost:8000/clubs/dashboard/' to your dashboard view logic
    path('dashboard/', views.ClubManagerDashboardView.as_view(), name='manager_dashboard'),
    path('player/add/', views.AddPlayerView.as_view(), name='add_player'),
]