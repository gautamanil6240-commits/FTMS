from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class ViewerRegisterForm(UserCreationForm):

    class Meta:
        model = User
        fields = [
            'username',
            'email',
        ]


class PlayerRegisterForm(UserCreationForm):

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'phone_number',
            'date_of_birth',
            'jersey_number',
            'preferred_position',
            'medical_status',
            'citizenship_document',
        ]


class CoachRegisterForm(UserCreationForm):

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'phone_number',
            'coach_license',
            'experience_certificate',
            'citizenship_document',
        ]


class ClubRegisterForm(UserCreationForm):

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'phone_number',
            'club_logo',
            'government_registration',
            'pan_number',
            'address',
            'founded_year',
        ]


class OrganizerRegisterForm(UserCreationForm):

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'phone_number',
            'organizer_logo',
            'authorization_letter',
            'pan_number',
            'office_address',
            'tournament_name',
        ]