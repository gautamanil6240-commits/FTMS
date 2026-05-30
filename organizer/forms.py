from django import forms
from .models import Tournament


class TournamentForm(forms.ModelForm):

    class Meta:

        model = Tournament

        fields = [

            'name',
            'tournament_type',
            'season',
            'start_date',
            'end_date',
            'location',
            'description',
            'logo',

        ]

        widgets = {

            'start_date': forms.DateInput(
                attrs={'type': 'date'}
            ),

            'end_date': forms.DateInput(
                attrs={'type': 'date'}
            ),

        }