from django.urls import path
from . import views

app_name = 'coach' 

urlpatterns = [
    path('register/', views.register_coach_view, name='register_coach_view'),
    path('login/', views.login_coach_view, name='login_coach_view'),
    path('logout/', views.logout_coach_view, name='logout_coach_view'),
    path('dashboard/', views.coach_dashboard, name='coach_dashboard'),
    path('player/<str:player_id>/', views.player_detail_view, name='player_detail'),
    path('player/<int:pk>/', views.player_detail_by_pk, name='player_detail_pk'),
    path('player/<int:pk>/remove/', views.remove_player_from_roster, name='remove_player'),
]
