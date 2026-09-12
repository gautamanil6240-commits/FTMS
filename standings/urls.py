from django.urls import path

from . import views

app_name = 'standings'

urlpatterns = [
    path('<int:tournament_pk>/', views.tournament_standings, name='tournament_standings'),
]
