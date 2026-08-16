from django.urls import path
from . import views

app_name = 'face_ou_pile'

urlpatterns = [
    path('', views.face_ou_pile_game, name='game'),
]
