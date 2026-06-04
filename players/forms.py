from django import forms
from .models import Player

class PlayerRegistrationForm(forms.ModelForm):
    class Meta:
        model = Player
        # ⚡ Matches your exact Git model keys
        fields = [
            'full_name', 'profile_photo', 'date_of_birth', 'gender', 
            'nationality', 'phone_number', 'email', 'citizenship_document',
            'preferred_position', 'jersey_number', 'height', 'weight', 'medical_status'
        ]
        
        # Consistent bootstrap control layouts
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First & Last Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'player@example.com'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '98XXXXXXXX'}),
            'nationality': forms.TextInput(attrs={'class': 'form-control'}),
            'jersey_number': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 10'}),
            'height': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Height in cm', 'step': '0.01'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Weight in kg', 'step': '0.01'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'preferred_position': forms.Select(attrs={'class': 'form-control'}),
            'medical_status': forms.Select(attrs={'class': 'form-control'}),
            'profile_photo': forms.FileInput(attrs={'class': 'form-control'}),
            'citizenship_document': forms.FileInput(attrs={'class': 'form-control'}),
        }