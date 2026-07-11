from django import forms
from .models import Club

class ClubRegistrationForm(forms.ModelForm):
    class Meta:
        model = Club
        # Exclude 'manager' because we set it automatically from request.user
        exclude = ['manager', 'is_verified', 'created_at', 'updated_at']