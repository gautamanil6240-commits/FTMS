import re
from django import forms
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import CoachProfile
from datetime import datetime
from django.contrib.auth.models import User


# ==========================================
# INLINE PROFILE MAINTENANCE EDIT FORM
# ==========================================
class CoachProfileEditForm(forms.ModelForm):
    class Meta:
        model = CoachProfile
        fields = ['full_name', 'phone_number', 'education', 'coaching_license', 'certificates', 'profile_photo']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'maxlength': '10', 'placeholder': '1234567890', 'class': 'form-control'}),
            'education': forms.TextInput(attrs={'class': 'form-control'}),
            'coaching_license': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.fields:
            self.fields[field_name].required = True

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        clean_phone = re.sub(r'\D', '', str(phone))
        if len(clean_phone) != 10:
            raise forms.ValidationError("Phone number must contain exactly 10 digits.")
        return clean_phone


# ==========================================
# REGISTER VIEW
# ==========================================
def register_coach_view(request):
    if request.method == 'POST':
        # Extract fields
        username          = request.POST.get('username', '').strip()
        email             = request.POST.get('email', '').strip()
        first_name        = request.POST.get('first_name', '').strip()
        last_name         = request.POST.get('last_name', '').strip()
        password          = request.POST.get('password', '')
        confirm_password  = request.POST.get('confirm_password', '')
        phone             = request.POST.get('phone', '').strip()
        dob_str           = request.POST.get('dob', '')
        gender            = request.POST.get('gender', '')
        nationality       = request.POST.get('nationality', '').strip()
        highest_education = request.POST.get('highest_education', '').strip()

        # Preserve inputs on error
        context = {
            'saved_inputs': {
                'username': username, 'email': email,
                'first_name': first_name, 'last_name': last_name,
                'phone': phone, 'dob': dob_str, 'gender': gender,
                'nationality': nationality, 'highest_education': highest_education,
            }
        }

        # --- Validation Rules ---

        # Rule A: All required fields filled
        if not all([username, email, first_name, last_name, password, confirm_password, phone, dob_str]):
            messages.error(request, "Please fill out all required fields.")
            return render(request, 'auth/register_coach.html', context)

        # Rule B: Passwords match
        if password != confirm_password:
            messages.error(request, "Passwords do not match. Please verify.")
            return render(request, 'auth/register_coach.html', context)

        # Rule C: Password strength
        if len(password) < 8 or not any(c.isdigit() for c in password):
            messages.error(request, "Password must be at least 8 characters and include a number.")
            return render(request, 'auth/register_coach.html', context)

        # Rule D: Username unique
        if User.objects.filter(username=username).exists():
            messages.error(request, "This username is already taken.")
            return render(request, 'auth/register_coach.html', context)

        # Rule E: Email unique
        if User.objects.filter(email=email).exists():
            messages.error(request, "An account with this email already exists.")
            return render(request, 'auth/register_coach.html', context)

        # Rule F: Phone must be exactly 10 digits
        clean_phone = re.sub(r'\D', '', phone)
        if len(clean_phone) != 10:
            messages.error(request, "Phone number must be exactly 10 digits.")
            return render(request, 'auth/register_coach.html', context)

        # Rule G: Age >= 18
        try:
            dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
            today = datetime.today().date()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            if age < 18:
                messages.error(request, "Coaches must be at least 18 years old.")
                return render(request, 'auth/register_coach.html', context)
        except ValueError:
            messages.error(request, "Invalid date of birth format.")
            return render(request, 'auth/register_coach.html', context)

        # --- All Validations Passed → Save to Database ---
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
            )
            CoachProfile.objects.create(
                user=user,
                full_name=f"{first_name} {last_name}",
                phone_number=clean_phone,
                date_of_birth=dob,
                gender=gender,
                nationality=nationality,
                education=highest_education,
                profile_photo=request.FILES.get('profile_photo'),
            )
            messages.success(request, f"Account created! Please log in, {first_name}.")
            # FIXED: Redirect targets the actual name of your login view route
            return redirect('coach:login_coach_view')

        except Exception as e:
            messages.error(request, f"Registration failed: {str(e)}")
            return render(request, 'auth/register_coach.html', context)

    return render(request, 'auth/register_coach.html')


# ==========================================
# LOGIN VIEW
# ==========================================
def login_coach_view(request):
    if request.user.is_authenticated:
        return redirect('coach:coach_dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        if not username or not password:
            messages.error(request, "Both username and password are required.")
            # FIXED: Points to 'auth/login.html' instead of 'login_coach.html'
            return render(request, 'auth/login.html', {'saved_username': username})

        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Note: Verify your profile relation name below matches your model's related_name or lowercase model name
            if hasattr(user, 'coach_profile') or hasattr(user, 'coachprofile'):
                login(request, user)
                messages.success(request, f"Welcome back, {user.first_name}!")
                return redirect('coach:coach_dashboard')
            else:
                messages.error(request, "No coach profile found for this account.")
                return render(request, 'auth/login.html', {'saved_username': username})
        else:
            messages.error(request, "Invalid username or password.")
            return render(request, 'auth/login.html', {'saved_username': username})

    # FIXED: Points to 'auth/login.html' instead of 'login_coach.html'
    return render(request, 'auth/login.html')


# ==========================================
# LOGOUT VIEW
# ==========================================
def logout_coach_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    # FIXED: Targets your corrected login view name
    return redirect('coach:login_coach_view')

@login_required
def coach_dashboard(request):
    try:
        # Safely get the logged-in coach's profile record
        coach_profile = getattr(request.user, 'coach_profile', None) or request.user.coachprofile
    except Exception:
        messages.error(request, "Coach profile not found.")
        return redirect('coach:login_coach_view')

    # Import the Player model early so it's accessible across handlers
    from players.models import Player

    # 🟢 1. Handle POST Requests
    if request.method == 'POST':
        # Condition A: Adding selected players to your roster
        if 'add_to_roster' in request.POST:
            selected_player_ids = request.POST.getlist('selected_players')
            if selected_player_ids:
                # Safely check if the coach has an assigned club before linking
                if hasattr(coach_profile, 'club') and coach_profile.club:
                    Player.objects.filter(id__in=selected_player_ids).update(club=coach_profile.club)
                    messages.success(request, f"Successfully added {len(selected_player_ids)} player(s) to your squad roster!")
                else:
                    messages.error(request, "Your coach profile isn't linked to a Club. Cannot assign players.")
            else:
                messages.warning(request, "No players were selected.")
            return redirect('coach:coach_dashboard')
        
        # Condition B: Handling existing coach profile edits
        else:
            form = CoachProfileEditForm(request.POST, request.FILES, instance=coach_profile)
            if form.is_valid():
                form.save()
                messages.success(request, "Profile updated successfully!")
                return redirect('coach:coach_dashboard')
            else:
                messages.error(request, "Please correct the profile errors below.")
                # DO NOT REDIRECT on form invalid errors, so error annotations show up!
    
    # 🟢 2. Handle GET Requests (Initial page load)
    else:
        form = CoachProfileEditForm(instance=coach_profile)

    # 🟢 3. Fetch all available players from the system who don't belong to any club yet
    # This guarantees 'available_players' is ALWAYS evaluated and filled for rendering
    available_players = Player.objects.all()

    return render(request, 'coach/coach_dashboard.html', {
        'coach': coach_profile,
        'form': form,
        'available_players': available_players, # Sent to template layout cleanly
    })