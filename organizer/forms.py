from django import forms
from .models import Tournament


class TournamentForm(forms.ModelForm):

    class Meta:

        model = Tournament

        fields = [
            'name',
            'description',
            'location',
            'banner',
            'start_date',
            'end_date',
            'format',
            'max_teams',
            'players_per_team',
            'prize_first',
            'prize_second',
            'prize_third',
            'rules',
        ]

        widgets = {

            'start_date': forms.DateInput(
                attrs={'type': 'date'}
            ),

            'end_date': forms.DateInput(
                attrs={'type': 'date'}
            ),

            'description': forms.Textarea(
                attrs={'rows': 4}
            ),

            'rules': forms.Textarea(
                attrs={'rows': 6}
            ),
        }