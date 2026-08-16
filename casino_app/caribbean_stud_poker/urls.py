from django.urls import path
from . import views

app_name = 'caribbean_stud_poker'
urlpatterns = [path('', views.caribbean_stud_poker_game, name='game')]