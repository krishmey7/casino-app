from django.urls import path
from . import views

app_name = 'double_exposure_blackjack'
urlpatterns = [path('', views.double_exposure_blackjack_game, name='game')]