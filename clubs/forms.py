from django import forms
from .models import Club

class ClubRegistrationForm(forms.ModelForm):
    class Meta:
        model = Club
        # Explicitly list the fields you want the manager to fill out during registration/setup
        fields = ['club_name', 'logo', 'description']
        widgets = {
            'club_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Club Name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Brief club history or description'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
        }