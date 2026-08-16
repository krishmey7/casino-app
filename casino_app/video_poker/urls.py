from django.urls import path
from . import views

app_name = 'video_poker'
urlpatterns = [path('', views.video_poker_game, name='game')]