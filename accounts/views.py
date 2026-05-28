from django.shortcuts import render, redirect

from django.contrib.auth import authenticate, login, logout

from django.contrib.auth.decorators import login_required

from .forms import CustomUserRegisterForm

from .models import CustomUser



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
    
def register_view(request):

    form = CustomUserRegisterForm()

    if request.method == 'POST':

        form = CustomUserRegisterForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            user = form.save(commit=False)

            user.is_active = True

            user.save()

            return redirect('login_selection')

    context = {

        'form': form

    }

    return render(

        request,
        'auth/register.html',
        context

    )
    
def login_view(request):

    if request.method == 'POST':

        username = request.POST.get('username')

        password = request.POST.get('password')

        user = authenticate(

            request,
            username=username,
            password=password

        )

        if user is not None:

            login(request, user)

            # ROLE REDIRECT

            if user.role == 'organizer':

                return redirect(
                    'organizer_dashboard'
                )

            elif user.role == 'manager':

                return redirect(
                    'manager_dashboard'
                )

            elif user.role == 'coach':

                return redirect(
                    'coach_dashboard'
                )

            elif user.role == 'player':

                return redirect(
                    'player_dashboard'
                )

            else:

                return redirect('home')

    return render(

        request,
        'auth/login.html'

    )
    
    
def logout_view(request):

    logout(request)

    return redirect('home')