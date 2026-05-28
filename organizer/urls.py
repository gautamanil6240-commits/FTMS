from django.urls import path             # type: ignore
from .views import organizer_dashboard      # type: ignore


urlpatterns = [

    path(
        'dashboard/',
        organizer_dashboard,
        name='organizer_dashboard'
    ),

]