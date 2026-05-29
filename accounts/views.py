from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

from .models import UserProfile


# =========================
# LOGIN SELECTION
# =========================

def login_selection(request):

    return render(
        request,
        'auth/login_selection.html'
    )


# =========================
# REGISTER
# =========================

def register(request, role):

    if request.method == 'POST':

        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 != password2:
            messages.error(request, "Passwords do not match")
            return redirect('register', role=role)

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect('register', role=role)

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1,
            first_name=first_name,
            last_name=last_name
        )

        profile = UserProfile.objects.create(
            user=user,
            role=role,
            phone_number=request.POST.get('phone_number'),

            # ORGANIZER
            organization_name=request.POST.get('organization_name'),
            pan_number=request.POST.get('pan_number'),
            tournament_name=request.POST.get('tournament_name'),
            office_address=request.POST.get('office_address'),

            # MANAGER
            club_name=request.POST.get('club_name'),
            founded_year=request.POST.get('founded_year'),
            club_address=request.POST.get('club_address'),

            # PLAYER
            date_of_birth=request.POST.get('date_of_birth') or None,
            jersey_number=request.POST.get('jersey_number'),
            preferred_position=request.POST.get('preferred_position'),
            medical_status=request.POST.get('medical_status') == '1',
        )

        # FILES

        profile.profile_photo = request.FILES.get('profile_photo')

        profile.organizer_logo = request.FILES.get('organizer_logo')
        profile.authorization_letter = request.FILES.get('authorization_letter')

        profile.club_logo = request.FILES.get('club_logo')
        profile.government_registration = request.FILES.get('government_registration')

        profile.coach_license = request.FILES.get('coach_license')
        profile.experience_certificate = request.FILES.get('experience_certificate')

        profile.citizenship_document = request.FILES.get('citizenship_document')

        profile.save()

        messages.success(
            request,
            "Registration submitted successfully. Wait for admin verification."
        )

        return redirect('login')

    return render(
        request,
        'auth/register.html',
        {
            'selected_role': role
        }
    )


# =========================
# LOGIN
# =========================

def user_login(request):

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

            return redirect('/')

        else:

            messages.error(
                request,
                "Invalid username or password"
            )

    return render(
        request,
        'auth/login.html'
    )


# =========================
# LOGOUT
# =========================

def user_logout(request):

    logout(request)

    return redirect('login')