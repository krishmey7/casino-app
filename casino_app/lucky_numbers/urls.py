from django.urls import path
from . import views

app_name = 'lucky_numbers'

urlpatterns = [
    path('', views.lucky_numbers_game, name='game'),
]
