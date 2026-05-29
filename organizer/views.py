from django.shortcuts import render


def organizer_dashboard(request):

    return render(
        request,
        'organizer/organizer_dashboard.html'
    )