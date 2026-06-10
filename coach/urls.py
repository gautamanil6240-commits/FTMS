from django.urls import path
from . import views

app_name = 'coach'

urlpatterns = [
    # 🏎️ This points cleanly to the dashboard function inside coach/views.py
    path('dashboard/', views.coach_dashboard, name='coach_dashboard'),
]