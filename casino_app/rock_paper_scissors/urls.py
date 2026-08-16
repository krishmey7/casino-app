from django.urls import path
from . import views

app_name = 'rock_paper_scissors'

urlpatterns = [
    path('', views.rock_paper_scissors_game, name='game'),
]