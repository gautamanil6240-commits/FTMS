from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render
from clubs.views import ClubManagerDashboardView

def home_view(request):
    return render(request, 'common/home.html')

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
]

# Media file asset streamer for profile photos and verification PDFs
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )