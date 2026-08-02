from django.urls import path
from . import views

urlpatterns = [

    # Organizer
    path(
        'dashboard/',
        views.organizer_dashboard,
        name='organizer_dashboard'
    ),

    path(
        'create-tournament/',
        views.create_tournament,
        name='create_tournament'
    ),

    # Public
    path(
        'tournaments/',
        views.tournament_list,
        name='tournament_list'
    ),

    path(
        'tournament/<int:pk>/',
        views.tournament_detail,
        name='tournament_detail'
    ),

    # Organizer view alias for dashboard table buttons
    path(
        'tournament/organizer/<int:pk>/',
        views.tournament_detail,
        name='organizer_tournament_detail'
    ),

]