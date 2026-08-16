from django.urls import path
from . import views

app_name = 'keno'

urlpatterns = [
    path('', views.keno_game, name='game'),
]