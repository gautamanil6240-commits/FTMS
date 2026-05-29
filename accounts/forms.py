from django import forms

from django.contrib.auth.forms import UserCreationForm

from .models import CustomUser


class CustomUserRegisterForm(UserCreationForm):

    class Meta:

        model = CustomUser

        fields = (

            'username',

            'email',

            'role',

            'phone',

            'profile_image',

            # ORGANIZER

            'pan_document',

            'organizer_letter',

            'club_logo',

            # MANAGER / COACH / PLAYER

            'citizenship_document',

            # COACH

            'coach_license',

            # PLAYER

            'medical_report',

            'password1',

            'password2',

        )

        widgets = {

            'username': forms.TextInput(

                attrs={
                    'placeholder': 'Username'
                }

            ),

            'email': forms.EmailInput(

                attrs={
                    'placeholder': 'Email'
                }

            ),

            'phone': forms.TextInput(

                attrs={
                    'placeholder': 'Phone Number'
                }

            ),

        }