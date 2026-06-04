from django.urls import path
from . import views

urlpatterns = [
    # This maps the path right to your view function
    path('register/player/', views.register_player, name='register_player'),
    path('dashboard/', views.player_dashboard, name='player_dashboard'),
]