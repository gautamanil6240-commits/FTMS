from django.urls import path
from . import views

app_name = 'players'

urlpatterns = [
    path('register/<str:role>/', views.register, name='register'),
    path('dashboard/', views.player_dashboard, name='player_dashboard'),
    path('list/', views.player_list, name='player_list'),
    path('sign/<uuid:player_id>/', views.sign_player, name='sign_player'),
]