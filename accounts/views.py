import re
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import UserProfile

# =========================
# LOGIN SELECTION
# =========================
def login_selection(request):
    return render(request, 'auth/login_selection.html')


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

        # Build standard authentication profile
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

        # =======================================================
        # AUTO CREATE CLUB ENGINE — Links Manager to Club Instantly
        # =======================================================
        if role == 'manager':            
            from clubs.models import Club            
            raw_founded_year = request.POST.get('founded_year')
            parsed_year = None
            
            if raw_founded_year:
                try:
                    parsed_year = int(str(raw_founded_year)[:4])
                except (ValueError, TypeError):
                    parsed_year = 2026

            Club.objects.get_or_create(                
                manager=user,                
                defaults={                    
                    'name': request.POST.get('club_name') or f"{username}'s Club",                    
                    'founded_year': parsed_year,
                    'address': request.POST.get('club_address', ''),                    
                    'government_registration': request.FILES.get('government_registration'),                    
                    'logo': request.FILES.get('club_logo'),                
                }            
            )

        # =======================================================
        # 🧠 FIXED: COACH EXTENSION INSTANTIATION ENGINE (SINGULAR)
        # =======================================================
        elif role == 'coach':
            from coach.models import CoachProfile  # ⚙️ Changed from 'coaches.models' to 'coach.models'

            raw_phone = request.POST.get('phone_number', '')
            clean_phone = re.sub(r'\D', '', str(raw_phone))[:10]
            if not clean_phone or len(clean_phone) < 10:
                clean_phone = "0000000000"

            CoachProfile.objects.create(
                user=user,
                full_name=f"{first_name} {last_name}".strip() or username,
                date_of_birth=request.POST.get('date_of_birth') or '2000-01-01',
                gender=request.POST.get('gender') or 'O',
                nationality=request.POST.get('nationality') or 'Unknown',
                profile_photo=request.FILES.get('profile_photo'),
                phone_number=clean_phone,
                education=request.POST.get('education', ''),
                coaching_license=request.POST.get('coaching_license', ''),
                certificates=request.FILES.get('experience_certificate')
            )

        messages.success(request, "Registration submitted successfully. Wait for admin verification.")
        return redirect('login')

    return render(request, f'auth/register_{role}.html')


# =========================
# LOGIN
# =========================
def user_login(request):
    role = request.GET.get('role', '')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            try:
                profile = UserProfile.objects.get(user=user)

                # Guardrail: Check verification state
                if not profile.is_verified:
                    messages.error(request, "Your account is awaiting admin approval.")
                    logout(request)
                    return redirect('login')

                if profile.role == 'organizer':
                    return redirect('organizer_dashboard')
                elif profile.role == 'manager':
                    return redirect('clubs:manager_dashboard')
                elif profile.role == 'coach':
                    return redirect('coach:coach_dashboard')
                elif profile.role == 'player':
                    return redirect('players:player_dashboard')
                elif profile.role == 'viewer':
                    return redirect('viewer_dashboard')
                    
            except UserProfile.DoesNotExist:
                from players.models import Player
                if Player.objects.filter(email=user.email).exists():
                    return redirect('players:player_dashboard')

                if user.is_superuser:
                    return redirect('/admin/')

            return redirect('/')
        else:
            messages.error(request, "Invalid username or password")

    return render(request, 'auth/login.html', {'role': role})


# =========================
# TOURNAMENT LIST
# =========================
def tournament_list(request):
    from organizer.models import Tournament
    try:
        tournaments = Tournament.objects.all().order_by('-created_at')
    except Exception:
        tournaments = Tournament.objects.all()
    return render(request, 'common/tournament_list.html', {'tournaments': tournaments})


# =========================
# LOGOUT
# =========================
def user_logout(request):
    logout(request)
    return redirect('login')