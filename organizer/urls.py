from django.urls import path

from . import views


urlpatterns = [

    path(
        'dashboard/',
        views.organizer_dashboard,
        name='organizer_dashboard'
    ),

]