from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import RoulettePartieViewSet

router = DefaultRouter()
router.register(r'parties', RoulettePartieViewSet, basename='roulette-parties')

urlpatterns = [
    path('', include(router.urls)),
]
