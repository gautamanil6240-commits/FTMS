from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class ViewerRegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email']

class PlayerRegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email']

class CoachRegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email']

class ClubRegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email']

class OrganizerRegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email']