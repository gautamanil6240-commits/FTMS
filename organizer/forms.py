from django import forms
from .models import Tournament


class TournamentForm(forms.ModelForm):

    class Meta:

        model = Tournament

        fields = [
            'name', 'description', 'location', 'banner',
            'start_date', 'end_date',
            'format', 'max_teams', 'players_per_team',
            'prize_first', 'prize_second', 'prize_third',
            'rules',
            # Contact & administration
            'contact_person', 'phone',
            'registration_type', 'status',
            # Category rules
            'age_category', 'gender_category',
            # Extra awards & medals
            'award_trophy', 'award_medals', 'award_certificate',
            'award_best_player', 'award_top_scorer',
            'award_best_goalkeeper', 'award_fair_play',
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

    def clean(self):
        cleaned_data = super().clean()

        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date and end_date < start_date:
            self.add_error(
                'end_date',
                'Registration close date must be on or after the registration open date.'
            )

        return cleaned_data
