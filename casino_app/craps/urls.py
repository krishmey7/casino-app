from django.urls import path
from . import views

app_name = 'craps'

urlpatterns = [
    path('', views.craps_game, name='game'),
]