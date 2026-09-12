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

    # Organizer edit / delete tournament
    path(
        'tournament/<int:pk>/edit/',
        views.edit_tournament,
        name='edit_tournament'
    ),

    path(
        'tournament/<int:pk>/delete/',
        views.delete_tournament,
        name='delete_tournament'
    ),

    # Club manager registers their club for a tournament
    path(
        'register-tournament/<int:tournament_pk>/',
        views.register_club_for_tournament,
        name='organizer_register_tournament'
    ),

    # Organizer approval queue
    path(
        'approvals/',
        views.approve_registrations,
        name='approve_registrations'
    ),

    path(
        'approvals/<int:registration_pk>/<str:action>/',
        views.review_registration,
        name='review_registration'
    ),

    # Group + Knockout management
    path(
        'tournament/<int:tournament_pk>/distribute-groups/',
        views.distribute_groups_view,
        name='distribute_groups'
    ),
    path(
        'tournament/<int:tournament_pk>/generate-group-schedule/',
        views.generate_group_schedule,
        name='generate_group_schedule'
    ),
    path(
        'tournament/<int:tournament_pk>/generate-bracket-from-groups/',
        views.generate_bracket_from_groups,
        name='generate_bracket_from_groups'
    ),

]
