from django.urls import path
from . import views

# This MUST match the namespace string in your main urls.py
app_name = 'coach' 

urlpatterns = [
    path('register/', views.register_coach_view, name='register_coach_view'),
    path('login/', views.login_coach_view, name='login_coach_view'),
    path('logout/', views.logout_coach_view, name='logout_coach_view'),
    path('dashboard/', views.coach_dashboard, name='coach_dashboard'),
]