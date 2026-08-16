from django.urls import path
from . import views

app_name = 'sic_bo'

urlpatterns = [
    path('', views.sic_bo_game, name='game'),
]