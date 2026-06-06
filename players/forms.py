from datetime import date
from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from .models import Player

class PlayerRawRegistrationForm(forms.Form):
    # Core Account Authentication Fields
    username = forms.CharField(max_length=150)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    
    # Personal & Athletic Profile Fields
    full_name = forms.CharField(max_length=255)
    dob = forms.DateField()
    gender = forms.ChoiceField(choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')])
    nationality = forms.CharField(max_length=100)
    phone = forms.CharField(max_length=20)
    position = forms.ChoiceField(choices=[('Goalkeeper', 'Goalkeeper'), ('Defender', 'Defender'), ('Midfielder', 'Midfielder'), ('Forward', 'Forward')])
    
    # Flexible, non-permanent numbering
    jersey_no = forms.CharField(max_length=10, required=False) 
    
    medical_status = forms.ChoiceField(choices=[('Fit', 'Fit'), ('Injured', 'Injured'), ('Suspended', 'Suspended')])
    height = forms.DecimalField(max_digits=5, decimal_places=2)
    weight = forms.DecimalField(max_digits=5, decimal_places=2)
    
    # Media & Identification Upload Fields
    profile_photo = forms.ImageField()
    id_document = forms.FileField()

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError("This username is already taken. Please choose another.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("A user with this email address already exists.")
        return email

    def clean_dob(self):
        dob = self.cleaned_data.get('dob')
        if dob and dob > date.today():
            raise ValidationError("Date of birth cannot be in the future.")
        return dob


class PlayerProfileEditForm(forms.ModelForm):
    class Meta:
        model = Player
        fields = [
            'full_name', 'profile_photo', 'phone_number', 
            'date_of_birth', 'gender', 'citizenship_document',
            'preferred_position', 'preferred_jersey_number', 
            'height', 'weight'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-input'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-input'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-input'}),
            'preferred_position': forms.Select(attrs={'class': 'form-input'}),
            'preferred_jersey_number': forms.NumberInput(attrs={'class': 'form-input'}),
            'height': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.1'}),
            'weight': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.1'}),
        }