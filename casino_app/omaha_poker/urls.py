from django.urls import path
from . import views

app_name = 'omaha_poker'
urlpatterns = [path('', views.omaha_poker_game, name='game')]