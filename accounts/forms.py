from django import forms

from django.contrib.auth.forms import UserCreationForm

from .models import CustomUser


class CustomUserRegisterForm(UserCreationForm):

    class Meta:

        model = CustomUser

        fields = [

            'first_name',
            'last_name',
            'username',
            'email',
            'phone_number',
            'role',
            'profile_photo',
            'password1',
            'password2',

        ]