from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from datetime import date

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
    
    # Changed from IntegerField to CharField for flexible, non-permanent numbering
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