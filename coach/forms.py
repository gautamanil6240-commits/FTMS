import re
from django import forms
from django.contrib.auth.models import User
from .models import CoachProfile, PlayerPerformance

class CoachRegistrationForm(forms.ModelForm):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    class Meta:
        model = CoachProfile
        fields = [
            'full_name', 'date_of_birth', 'gender', 'nationality', 'profile_photo',
            'phone_number', 'education', 'coaching_license', 'certificates'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'nationality': forms.TextInput(attrs={'class': 'form-control'}),
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
            raise forms.ValidationError("The phone number must contain exactly 10 digits.")
        return clean_phone

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email address is already registered.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        username = cleaned_data.get("username")

        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match!")

        if username and User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken.")

        return cleaned_data


# ==========================================
# PROFILE MAINTENANCE EDIT FORM 
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
            raise forms.ValidationError("The phone number must contain exactly 10 digits.")
        return clean_phone


# ==========================================
# PLAYER PERFORMANCE LOGGING FORM
# (Used by coaches to log per-match stats / reviews)
# ==========================================
class PlayerPerformanceForm(forms.ModelForm):
    class Meta:
        model = PlayerPerformance
        fields = ['performance_date', 'match_title', 'goals', 'assists', 'minutes_played', 'rating', 'notes']
        widgets = {
            'performance_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'match_title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. vs. FC Eagles'}),
            'goals': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'assists': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'minutes_played': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'rating': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Coach comments, fitness notes, tactical observations...'}),
        }

