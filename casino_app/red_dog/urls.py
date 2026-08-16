from django.urls import path
from . import views

app_name = 'red_dog'
urlpatterns = [path('', views.red_dog_game, name='game')]