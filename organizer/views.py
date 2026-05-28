from django.shortcuts import render    # type: ignore

# Create your views here.

def organizer_dashboard(request):

    return render(
        request,
        'organizer/organizer_dashboard.html'
    )