from django.urls import path
from . import views

app_name = 'spanish_21'
urlpatterns = [path('', views.spanish_21_game, name='game')]