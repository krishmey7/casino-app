from django.urls import path
from . import views

app_name = 'texas_holdem'
urlpatterns = [path('', views.texas_holdem_game, name='game')]