from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import PokerGameViewSet

router = DefaultRouter()
router.register(r'games', PokerGameViewSet)

urlpatterns = [
    path('', include(router.urls)),
]