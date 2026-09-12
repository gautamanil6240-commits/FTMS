from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render
from django.utils import timezone
from django.db import models as db_models
from datetime import timedelta
from clubs.views import ClubManagerDashboardView

def home_view(request):
    from organizer.models import Tournament

    cutoff = timezone.now() - timedelta(days=10)

    upcoming = Tournament.objects.filter(
        status__in=['registration', 'upcoming']
    ).order_by('start_date')[:6]

    ongoing = Tournament.objects.filter(
        status='active'
    ).order_by('start_date')[:6]

    finished = Tournament.objects.filter(
        status='completed'
    ).filter(
        db_models.Q(completed_at__gte=cutoff) | db_models.Q(completed_at__isnull=True)
    ).order_by('-completed_at')[:6]

    return render(request, 'common/home.html', {
        'upcoming_tournaments': upcoming,
        'ongoing_tournaments': ongoing,
        'finished_tournaments': finished,
    })

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Home Landing Portal
    path('', home_view, name='home'),

    # Accounts Authentication Flow
    path('accounts/', include('accounts.urls')),
    
    # Isolated the players app to prevent URL prefix collisions
    path('players/', include('players.urls')),

    # Organizer Portal
    path('organizer/', include('organizer.urls')),

    # Club Management Portal
    path('clubs/', include('clubs.urls')),
    path('manager/dashboard/', ClubManagerDashboardView.as_view(), name='manager_dashboard'),

    # Coach portal
    path('coach/', include('coach.urls', namespace='coach')),

    # Match schedule generator and fixture planner
    path('matches/', include('matches.urls')),

    # Public league standings
    path('standings/', include('standings.urls')),

    # Comments
    path('comments/', include('comments.urls')),

    # Notifications
    path('notifications/', include('notifications.urls')),
]

# Media file asset streamer for profile photos and verification PDFs
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )