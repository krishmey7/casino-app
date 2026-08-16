from django.urls import path
from . import views

app_name = 'let_it_ride'
urlpatterns = [path('', views.let_it_ride_game, name='game')]