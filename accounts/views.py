from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import CustomUser


def home(request):
    return render(request, 'common/home.html')


def login_selection(request):
    return render(request, 'auth/login_selection.html')


# ===== LOGIN VIEWS =====
def organizer_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user and user.role == 'organizer':
            if user.approved:
                login(request, user)
                return redirect('organizer_dashboard')
            else:
                messages.error(request, '⚠️ Account pending admin approval.')
        else:
            messages.error(request, '❌ Invalid credentials.')
    return render(request, 'auth/login.html', {'role': 'Organizer'})


def manager_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user and user.role == 'manager':
            if user.approved:
                login(request, user)
                return redirect('home')
            else:
                messages.error(request, '⚠️ Account pending admin approval.')
        else:
            messages.error(request, '❌ Invalid credentials.')
    return render(request, 'auth/login.html', {'role': 'Manager'})


def coach_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user and user.role == 'coach':
            if user.approved:
                login(request, user)
                return redirect('home')
            else:
                messages.error(request, '⚠️ Account pending admin approval.')
        else:
            messages.error(request, '❌ Invalid credentials.')
    return render(request, 'auth/login.html', {'role': 'Coach'})


def player_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user and user.role == 'player':
            if user.approved:
                login(request, user)
                return redirect('home')
            else:
                messages.error(request, '⚠️ Account pending admin approval.')
        else:
            messages.error(request, '❌ Invalid credentials.')
    return render(request, 'auth/login.html', {'role': 'Player'})


def viewer_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user and user.role == 'viewer':
            if user.approved:
                login(request, user)
                return redirect('home')
            else:
                messages.error(request, '⚠️ Account pending admin approval.')
        else:
            messages.error(request, '❌ Invalid credentials.')
    return render(request, 'auth/login.html', {'role': 'Viewer'})


# ===== REGISTER =====
def register_view(request):
    if request.method == 'POST':
        role       = request.POST.get('role')
        username   = request.POST.get('username')
        email      = request.POST.get('email')
        password1  = request.POST.get('password1')
        password2  = request.POST.get('password2')
        first_name = request.POST.get('first_name')
        last_name  = request.POST.get('last_name')
        phone      = request.POST.get('phone_number')

        if password1 != password2:
            messages.error(request, '❌ Passwords do not match!')
            return redirect('register')

        if len(password1) < 8:
            messages.error(request, '❌ Password must be at least 8 characters!')
            return redirect('register')

        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, '❌ Username already taken!')
            return redirect('register')

        user = CustomUser(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone_number=phone,
            role=role,
            approved=False,
        )
        user.set_password(password1)

        if 'profile_photo' in request.FILES:
            user.profile_photo = request.FILES['profile_photo']
        if 'club_logo' in request.FILES:
            user.club_logo = request.FILES['club_logo']
        if 'government_reg_cert' in request.FILES:
            user.government_reg_cert = request.FILES['government_reg_cert']
        if 'organization_letter' in request.FILES:
            user.organization_letter = request.FILES['organization_letter']
        if 'citizenship_photo' in request.FILES:
            user.citizenship_photo = request.FILES['citizenship_photo']

        user.club_name    = request.POST.get('club_name', '')
        user.pan_number   = request.POST.get('pan_number', '')
        user.club_address = request.POST.get('club_address', '')
        user.founded_year = request.POST.get('founded_year', '')
        user.date_of_birth = request.POST.get('date_of_birth') or None

        user.save()
        messages.success(
            request,
            '✅ Registration successful! Wait for admin approval.'
        )
        return redirect('login_selection')

    return render(request, 'auth/register.html')


# ===== DASHBOARD =====
def dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login_selection')
    role = request.user.role
    if role == 'organizer':
        return redirect('organizer_dashboard')
    return redirect('home')


# ===== LOGOUT =====
def logout_view(request):
    logout(request)
    messages.success(request, 'Logged out successfully!')
    return redirect('home')