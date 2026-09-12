from django.urls import path
from . import views

app_name = 'clubs'

urlpatterns = [
    # Club Manager URLs
    path('register/', views.ClubManagerRegisterView.as_view(), name='register_manager'),
    path('dashboard/', views.ClubManagerDashboardView.as_view(), name='manager_dashboard'),
    path('add-coach/', views.AddCoachView.as_view(), name='add_coach'),
    path('coach-lookup/', views.coach_lookup, name='coach_lookup'),
    path('registrations/', views.ClubRegistrationsView.as_view(), name='my_registrations'),
]
