import re
from django import forms
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import CoachProfile

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
        # Force all edit fields to be strictly required
        for field_name in self.fields:
            self.fields[field_name].required = True

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        clean_phone = re.sub(r'\D', '', str(phone))
        if len(clean_phone) != 10:
            raise forms.ValidationError("The phone number must contain exactly 10 digits.")
        return clean_phone


# ==========================================
# DASHBOARD VIEW ENGINE
# ==========================================
@login_required
def coach_dashboard(request):
    try:
        # Fetch the profile belonging to the logged-in user
        coach_profile = request.user.coach_profile
    except CoachProfile.DoesNotExist:
        messages.error(request, "Coach profile data could not be located.")
        return redirect('login')

    if request.method == 'POST':
        form = CoachProfileEditForm(request.POST, request.FILES, instance=coach_profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been securely updated!")
            return redirect('coach:coach_dashboard')
        else:
            messages.error(request, "Please correct the formatting errors below.")
    else:
        form = CoachProfileEditForm(instance=coach_profile)

    return render(request, 'coach/coach_dashboard.html', {
        'coach': coach_profile,
        'form': form
    })

