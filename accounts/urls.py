from django.urls import path
from . import views


urlpatterns = [

    path(
        'login-selection/',
        views.login_selection,
        name='login_selection'
    ),

    path(
        'register/<str:role>/',
        views.register,
        name='register'
    ),

    path(
        'login/',
        views.user_login,
        name='login'
    ),

    path(
        'logout/',
        views.user_logout,
        name='logout'
    ),

]