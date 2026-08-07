from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.urls import reverse_lazy
from django.contrib.auth.views import PasswordResetView
from .models import UserProfile
from .forms import CustomPasswordResetForm
from django.contrib.auth.decorators import login_required
from organizer.models import Tournament
from players.models import Player as PlayerModel
from clubs.models import Club, get_or_create_manager_club

def get_redirect_for_user(user):
    try:
        profile = UserProfile.objects.get(user=user)
        if profile.role == 'organizer': return redirect('organizer_dashboard')
        if profile.role == 'manager':
            # Ensure a Club record exists for this manager (auto-create if
            # missing, e.g. accounts created before Club linkage was added).
            get_or_create_manager_club(user)
            return redirect('manager_dashboard')
        if profile.role == 'coach': return redirect('coach:coach_dashboard')
        if profile.role == 'player': return redirect('players:player_dashboard')
        if profile.role == 'viewer': return redirect('viewer:viewer_dashboard')
    except UserProfile.DoesNotExist:
        if user.is_superuser: return redirect('/admin/')
    return redirect('home')

# =========================
# LOGIN SELECTION
# =========================

def login_selection(request):
    if request.user.is_authenticated:
        try:
            profile = UserProfile.objects.get(user=request.user)
            role = profile.role
        except UserProfile.DoesNotExist:
            role = 'admin' if request.user.is_superuser else 'user'
        
        return render(request, 'auth/already_logged_in.html', {
            'role': role,
            'user': request.user,
        })
    
    return render(request, 'auth/login_selection.html')

# =========================
# REGISTER
# =========================

def register(request):
    role = request.GET.get('role')
    if not role:
        return redirect('login_selection')
    
    if request.user.is_authenticated:
        return get_redirect_for_user(request.user)

    if request.method == 'POST':
        username = request.POST.get('username')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 != password2:
            messages.error(request, "Passwords do not match")
            return redirect(f'/accounts/register/?role={role}')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect(f'/accounts/register/?role={role}')

        # Fallback values to prevent MySQL null errors on first_name/last_name
        first_name = request.POST.get('first_name') or username
        last_name = request.POST.get('last_name') or ''

        user = User.objects.create_user(
            username=username,
            email=request.POST.get('email'),
            password=password1,
            first_name=first_name,
            last_name=last_name
        )

        profile = UserProfile.objects.create(
            user=user,
            role=role,
            phone_number=request.POST.get('phone_number') or request.POST.get('phone'),
            organization_name=request.POST.get('organization_name'),
            pan_number=request.POST.get('pan_number'),
            tournament_name=request.POST.get('tournament_name'),
            office_address=request.POST.get('office_address'),
            club_name=request.POST.get('club_name'),
            founded_year=request.POST.get('founded_year') or None,
            club_address=request.POST.get('club_address') or request.POST.get('club_city'),
            date_of_birth=request.POST.get('date_of_birth') or None,
            jersey_number=request.POST.get('jersey_number'),
            preferred_position=request.POST.get('preferred_position'),
            medical_status=request.POST.get('medical_status') == '1',
        )
        
        # Files handling including organizer and manager specific file fields
        fields = ['profile_photo', 'organizer_logo', 'authorization_letter', 'organization_document',
                  'club_logo', 'government_registration', 'coach_license', 
                  'experience_certificate', 'citizenship_document',
                  'pan_document', 'government_document']
                  
        for field in fields:
            if field in request.FILES:
                setattr(profile, field, request.FILES[field])
        profile.save()

        # If the user registered as a manager, also create the Club record
        # so that request.user.managed_club works immediately.
        if role == 'manager':
            club_name = request.POST.get('club_name')
            club_city = request.POST.get('club_city') or request.POST.get('club_address')
            phone = request.POST.get('phone_number') or request.POST.get('phone')
            Club.objects.create(
                manager=user,
                name=club_name or profile.club_name,
                city=club_city or '',
                phone=phone or '',
                logo=request.FILES.get('club_logo'),
                pan_document=request.FILES.get('pan_document'),
                government_document=request.FILES.get('government_document'),
                citizenship_document=request.FILES.get('citizenship_document'),
                is_verified=False,
            )

        messages.success(request, "Registration submitted successfully. Wait for admin verification.")
        return redirect('login')

    return render(request, f'auth/register_{role}.html')

# =========================
# LOGIN
# =========================

def user_login(request):
    if request.user.is_authenticated:
        return get_redirect_for_user(request.user)

    role = request.GET.get('role', '')
    if request.method == 'POST':
        user = authenticate(request, username=request.POST.get('username'), password=request.POST.get('password'))

        if user is not None:
            try:
                profile = UserProfile.objects.get(user=user)
                if not profile.is_verified:
                    messages.error(request, "Your account is awaiting admin approval.")
                    return redirect(f'{reverse_lazy("login")}?role={role}')
                login(request, user)
                return get_redirect_for_user(user)
            except UserProfile.DoesNotExist:
                # Check if user has a coach_profile (registered via coach app)
                if hasattr(user, 'coach_profile'):
                    # Auto-create UserProfile for coach app users if missing
                    UserProfile.objects.create(
                        user=user,
                        role='coach',
                        is_verified=True,
                    )
                    login(request, user)
                    return redirect('coach:coach_dashboard')
                # Check if user has club_coach_profile (assigned by manager)
                if hasattr(user, 'club_coach_profile'):
                    # Auto-create UserProfile for manager-assigned coaches if missing
                    UserProfile.objects.create(
                        user=user,
                        role='coach',
                        is_verified=True,
                    )
                    login(request, user)
                    return redirect('coach:coach_dashboard')
                # Check if user is a Player (has Player record matching their email)
                if PlayerModel.objects.filter(email=user.email).exists():
                    player = PlayerModel.objects.get(email=user.email)
                    UserProfile.objects.create(
                        user=user,
                        role='player',
                        phone_number=player.phone_number or '',
                        is_verified=True,
                        date_of_birth=player.date_of_birth,
                    )
                    login(request, user)
                    return redirect('players:player_dashboard')
                # Check if user is a Club Manager (has managed_club relation)
                if hasattr(user, 'managed_club'):
                    club = user.managed_club
                    UserProfile.objects.create(
                        user=user,
                        role='manager',
                        phone_number=club.phone or '',
                        is_verified=True,
                        club_name=club.name,
                        club_address=club.city or '',
                    )
                    login(request, user)
                    return redirect('manager_dashboard')
                if user.is_superuser:
                    login(request, user)
                    return redirect('/admin/')
                # If no profile found at all, show error
                messages.error(request, "Your account has no role assigned. Please contact support.")
                return redirect(f'{reverse_lazy("login")}?role={role}')
        else:
            messages.error(request, "Invalid username or password")

    return render(request, 'auth/login.html', {
        'role': role,
        'post_url': 'login',
    })

# =========================
# TOURNAMENT LIST
# =========================

def tournament_list(request):
    tournaments = Tournament.objects.all().order_by('-created_at')
    return render(request, 'organizer/tournament_list.html', {'tournaments': tournaments})

# =========================
# PASSWORD RESET & LOGOUT
# =========================

class CustomPasswordResetView(PasswordResetView):
    form_class = CustomPasswordResetForm
    template_name = 'auth/password_reset.html'
    success_url = reverse_lazy('password_reset_done')

def user_logout(request):
    logout(request)
    return redirect('login')
