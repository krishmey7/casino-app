from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import LuckyNumberGameViewSet, LuckyNumberBetViewSet

router = DefaultRouter()
router.register(r'games', LuckyNumberGameViewSet)
router.register(r'bets', LuckyNumberBetViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
