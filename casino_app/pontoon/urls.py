from django.urls import path
from . import views

app_name = 'pontoon'
urlpatterns = [path('', views.pontoon_game, name='game')]