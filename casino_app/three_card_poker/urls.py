from django.urls import path
from . import views

app_name = 'three_card_poker'
urlpatterns = [path('', views.three_card_poker_game, name='game')]