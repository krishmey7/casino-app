from django.urls import path
from . import views

app_name = 'blackjack'

urlpatterns = [
    path('', views.blackjack_game, name='game'),
]
