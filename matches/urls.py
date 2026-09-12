from django.urls import path

from . import views

app_name = 'matches'

urlpatterns = [
    path('generate/<int:tournament_pk>/', views.generate_schedule, name='generate_schedule'),
    path('schedule/<int:tournament_pk>/', views.view_edit_schedule, name='schedule'),
    path('result/<int:match_pk>/', views.enter_match_result, name='enter_match_result'),
    path('cancel/<int:match_pk>/', views.cancel_match, name='cancel_match'),
    path('uncancel/<int:match_pk>/', views.uncancel_match, name='uncancel_match'),
    path('match/<int:match_pk>/', views.match_detail, name='match_detail'),
    path('bracket/<int:tournament_pk>/', views.bracket_view, name='bracket_view'),
]
