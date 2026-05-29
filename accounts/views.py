from django.shortcuts import render


def home(request):

    return render(
        request,
        'common/home.html'
    )


def login_selection(request):

    return render(
        request,
        'auth/login_selection.html'
    )


def organizer_login(request):

    return render(
        request,
        'auth/login.html',
        {
            'role': 'Organizer'
        }
    )


def manager_login(request):

    return render(
        request,
        'auth/login.html',
        {
            'role': 'Manager'
        }
    )


def coach_login(request):

    return render(
        request,
        'auth/login.html',
        {
            'role': 'Coach'
        }
    )


def player_login(request):

    return render(
        request,
        'auth/login.html',
        {
            'role': 'Player'
        }
    )


def viewer_login(request):

    return render(
        request,
        'auth/login.html',
        {
            'role': 'Viewer'
        }
    )