from django.urls import path
from . import views

app_name = 'fan_tan'
urlpatterns = [path('', views.fan_tan_game, name='game')]