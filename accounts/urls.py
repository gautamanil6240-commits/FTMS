from django.urls import path
from . import views

urlpatterns = [

    path(
        '',
        views.home,
        name='home'
    ),

    path(
        'login-selection/',
        views.login_selection,
        name='login_selection'
    ),

    path(
        'login/organizer/',
        views.organizer_login,
        name='organizer_login'
    ),

    path(
        'login/manager/',
        views.manager_login,
        name='manager_login'
    ),

    path(
        'login/coach/',
        views.coach_login,
        name='coach_login'
    ),

    path(
        'login/player/',
        views.player_login,
        name='player_login'
    ),

    path(
        'login/viewer/',
        views.viewer_login,
        name='viewer_login'
    ),

]