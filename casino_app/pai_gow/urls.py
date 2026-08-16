from django.urls import path
from . import views

app_name = 'pai_gow'

urlpatterns = [
    path('', views.pai_gow_game, name='game'),
]