from django.urls import path
from . import views

app_name = 'scratch_cards'
urlpatterns = [path('', views.scratch_cards_game, name='game')]