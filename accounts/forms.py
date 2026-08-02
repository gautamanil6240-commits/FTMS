from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordResetForm

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

class CustomPasswordResetForm(PasswordResetForm):
    def send_mail(self, subject_template_name, email_template_name, context, 
                  from_email, to_email, html_email_template_name=None):
        super().send_mail(subject_template_name, email_template_name, context, 
                from_email, to_email, html_email_template_name)        