from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import RockPaperScissorsGameViewSet

router = DefaultRouter()
router.register(r'games', RockPaperScissorsGameViewSet)

urlpatterns = [
    path('', include(router.urls)),
]