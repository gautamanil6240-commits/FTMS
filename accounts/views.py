from django.db import models             # type: ignore
from django.shortcuts import render       # type: ignore

# Create your views hefrom django.shortcuts import render

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