from django.urls import path, include
from .views import roulett_partie_vue

app_name = 'roulette'

urlpatterns = [
    path('', roulett_partie_vue, name='roulette_game'),
    path('api/', include('casino_app.roulette.api_urls')),
]
