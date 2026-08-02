from django.shortcuts import render, redirect
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model, login
from django.contrib import messages
from .models import Club, Coach, Player
from accounts.models import UserProfile
from coach.models import CoachProfile

User = get_user_model()

# =======================================================
# 1. CLUB MANAGER REGISTRATION VIEW
# =======================================================
class ClubManagerRegisterView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('clubs:manager_dashboard')
        return render(request, 'clubs/register_manager.html')

    def post(self, request):
        club_name = request.POST.get('club_name')
        city = request.POST.get('club_city')
        username = request.POST.get('username')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        # Files
        logo = request.FILES.get('club_logo')
        pan_doc = request.FILES.get('pan_document')
        govt_doc = request.FILES.get('government_document')
        cit_doc = request.FILES.get('citizenship_document')

        # Validation Checks
        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return redirect('clubs:register_manager')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username is already taken.")
            return redirect('clubs:register_manager')

        if Club.objects.filter(name=club_name).exists():
            messages.error(request, "A club with this name is already registered.")
            return redirect('clubs:register_manager')

        try:
            # Create User Account
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1
            )

            # Create Associated Club Profile
            Club.objects.create(
                manager=user,
                name=club_name,
                city=city,
                phone=phone,
                logo=logo,
                pan_document=pan_doc,
                government_document=govt_doc,
                citizenship_document=cit_doc
            )

            # Create UserProfile for login compatibility
            UserProfile.objects.create(
                user=user,
                role='manager',
                phone_number=phone or '',
                is_verified=True,
                club_name=club_name,
                club_address=city or '',
            )

            # Log the user in directly after successful sign-up
            login(request, user)
            messages.success(request, "Club registration submitted successfully! Welcome to your manager dashboard.")
            return redirect('clubs:manager_dashboard')

        except Exception as e:
            messages.error(request, f"Registration failed due to an error: {str(e)}")
            return redirect('clubs:register_manager')


# =======================================================
# 2. CLUB MANAGER DASHBOARD
# =======================================================
class ClubManagerDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'clubs/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            club = self.request.user.managed_club
            context['club'] = club
            context['coaches'] = club.club_coaches.all()
            context['has_club'] = True
        except (Club.DoesNotExist, AttributeError):
            context['has_club'] = False
        return context


# =======================================================
# 3. COACH DASHBOARD
# =======================================================
class CoachDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'clubs/coach_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            coach = self.request.user.club_coach_profile
            context['coach'] = coach
            context['players'] = coach.players.all()
            context['has_coach_profile'] = True
        except AttributeError:
            context['has_coach_profile'] = False
            context['players'] = []
        return context


# =======================================================
# 4. COACH ADD PLAYER VIEW
# =======================================================
class CoachAddPlayerView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'clubs/add_player.html')

    def post(self, request):
        try:
            coach = request.user.club_coach_profile
        except AttributeError:
            messages.error(request, "Only assigned coaches can add players to a roster.")
            return redirect('home')

        name = request.POST.get('name')
        jersey_no = request.POST.get('jersey_number')
        position = request.POST.get('position')

        if coach.players.filter(jersey_number=jersey_no).exists():
            messages.error(request, f"Jersey number #{jersey_no} is already assigned in your squad.")
            return render(request, 'clubs/add_player.html')

        Player.objects.create(
            coach=coach,
            full_name=name,
            jersey_number=jersey_no,
            position=position
        )
        
        messages.success(request, f"Successfully registered player {name}!")
        return redirect('clubs:coach_dashboard')


# =======================================================
# 5. ADD COACH VIEW
# =======================================================

class AddCoachView(LoginRequiredMixin, View):
    def get(self, request):
        try:
            club = request.user.managed_club
        except Exception as e:
            from django.http import HttpResponse
            return HttpResponse(f"DEBUG GET ERROR: {e} | User: {request.user} (ID: {request.user.id})")
        
        return render(request, 'clubs/add_coach.html', {
            'club': club,
            'coaches': club.club_coaches.all(),
        })

    def post(self, request):
        try:
            club = request.user.managed_club
        except Exception as e:
            from django.http import HttpResponse
            return HttpResponse(f"DEBUG POST ERROR: {e} | User: {request.user} (ID: {request.user.id})")

        full_name = request.POST.get('full_name')
        license_level = request.POST.get('license_level')
        coach_id_number = request.POST.get('coach_id_number')
        email = request.POST.get('email')
        phone = request.POST.get('phone')

        context = {
            'club': club,
            'coaches': club.club_coaches.all(),
        }

        if not coach_id_number or not coach_id_number.startswith('coa'):
            messages.error(request, "Coach Unique Code must start with 'coa' (e.g. coa65674).")
            return render(request, 'clubs/add_coach.html', context)

        if Coach.objects.filter(coach_id_number=coach_id_number).exists():
            messages.error(request, "A coach with this unique code already exists.")
            return render(request, 'clubs/add_coach.html', context)

        # Check if a User with this coach_id_number as username already exists
        username = f"coach_{coach_id_number.replace('coa', '')}"
        if User.objects.filter(username=username).exists():
            messages.error(request, f"A user account for this coach already exists (username: {username}).")
            return render(request, 'clubs/add_coach.html', context)

        try:
            # 1. Create User account (password = coach_id_number as initial password)
            coach_user = User.objects.create_user(
                username=username,
                email=email or f"{username}@temp.com",
                password=coach_id_number,
                first_name=full_name.split()[0] if full_name.split() else full_name,
                last_name=' '.join(full_name.split()[1:]) if len(full_name.split()) > 1 else '',
            )

            # 2. Create UserProfile with role='coach' and auto-verified
            UserProfile.objects.create(
                user=coach_user,
                role='coach',
                phone_number=phone or '',
                is_verified=True,
                coach_id_number=coach_id_number,
                assigned_manager=request.user,
            )

            # 3. Create CoachProfile (for coach app login compatibility)
            CoachProfile.objects.create(
                user=coach_user,
                club=club,
                coach_id_number=coach_id_number,
                full_name=full_name,
                phone_number=phone or '',
            )

            # 4. Create clubs.Coach record (for manager dashboard compatibility)
            Coach.objects.create(
                user=coach_user,
                club=club,
                full_name=full_name,
                license_level=license_level,
                coach_id_number=coach_id_number,
                email=email,
                phone=phone
            )

            success_msg = (
                f"✅ Coach {full_name} assigned successfully!<br>"
                f"<strong>Login Credentials:</strong><br>"
                f"Username: <strong>{username}</strong><br>"
                f"Password: <strong>{coach_id_number}</strong>"
            )
            messages.success(request, success_msg)
            return redirect('clubs:add_coach')

        except Exception as e:
            messages.error(request, f"Error registering coach: {e}")
            return render(request, 'clubs/add_coach.html', context)
