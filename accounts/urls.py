from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Tournament List
    path(
        'tournaments/',
        views.tournament_list,
        name='tournament_list'
    ),

    # Login Selection
    path(
        'login-selection/',
        views.login_selection,
        name='login_selection'
    ),

    # Added: Register
    path(
        'register/',
        views.register,
        name='register'
    ),

    # Login
    path(
        'login/',
        views.user_login,
        name='login'
    ),

    # Logout
    path(
        'logout/',
        views.user_logout,
        name='logout'
    ),

    # Password Reset
    path(
        'password-reset/',
        auth_views.PasswordResetView.as_view(
            template_name='auth/password_reset.html',
            email_template_name='auth/password_reset_email.html',
            success_url='/password-reset/done/'
        ),
        name='password_reset'
    ),

    path(
        'password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='auth/password_reset_done.html'
        ),
        name='password_reset_done'
    ),

    path(
        'reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='auth/password_reset_confirm.html',
            success_url='/reset/done/' 
        ),
        name='password_reset_confirm'
    ),

    path(
        'reset/done/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='auth/password_reset_complete.html'
        ),
        name='password_reset_complete'
    ),
]