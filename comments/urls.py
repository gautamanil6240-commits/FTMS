from django.urls import path

from . import views

app_name = 'comments'

urlpatterns = [
    path(
        'tournament/<int:tournament_pk>/',
        views.add_tournament_comment,
        name='add_tournament_comment',
    ),
    path(
        'match/<int:match_pk>/',
        views.add_match_comment,
        name='add_match_comment',
    ),
]
