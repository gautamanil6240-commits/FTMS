from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser


class ViewerRegisterForm(UserCreationForm):

    class Meta:
        model = CustomUser
        fields = [
            'username',
            'email',
            'password1',
            'password2'
        ]


class PlayerRegisterForm(UserCreationForm):

    class Meta:
        model = CustomUser
        fields = [
            'username',
            'email',
            'phone_number',
            'date_of_birth',
            'jersey_number',
            'preferred_position',
            'medical_status',
            'citizenship_document',
            'password1',
            'password2'
        ]


class CoachRegisterForm(UserCreationForm):

    class Meta:
        model = CustomUser
        fields = [
            'username',
            'email',
            'phone_number',
            'coach_license',
            'experience_certificate',
            'citizenship_document',
            'password1',
            'password2'
        ]


class ClubRegisterForm(UserCreationForm):

    class Meta:
        model = CustomUser
        fields = [
            'club_name',
            'email',
            'phone_number',
            'club_logo',
            'government_registration',
            'pan_number',
            'address',
            'founded_year',
            'password1',
            'password2'
        ]


class OrganizerRegisterForm(UserCreationForm):

    class Meta:
        model = CustomUser
        fields = [
            'organization_name',
            'email',
            'phone_number',
            'organizer_logo',
            'authorization_letter',
            'pan_number',
            'office_address',
            'tournament_name',
            'password1',
            'password2'
        ]