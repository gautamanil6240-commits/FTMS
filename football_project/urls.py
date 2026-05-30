from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render


def home_view(request):
    return render(request, 'common/home.html')


urlpatterns = [

    # Admin
    path('admin/', admin.site.urls),

    # Home
    path('', home_view, name='home'),

    # Accounts
    path('', include('accounts.urls')),

    # Organizer
    path('organizer/', include('organizer.urls')),

]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )