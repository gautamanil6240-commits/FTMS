from django.db import models             # type: ignore
from django.urls import path         # type: ignore
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

]