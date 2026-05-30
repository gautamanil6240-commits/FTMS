from django.urls import path
from . import views

urlpatterns = [

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
    path(
    'tournament/<int:pk>/',
    views.organizer_tournament_detail,
    name='organizer_tournament_detail'
    ),

]