from django.urls import path
from . import views

app_name = 'casino_war'
urlpatterns = [path('', views.casino_war_game, name='game')]