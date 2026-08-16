from django.urls import path
from . import views

app_name = 'golitep'

urlpatterns = [
    path('', views.mines_game, name='game'),
]
