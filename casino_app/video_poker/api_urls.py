from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import VideoPokerGameViewSet

router = DefaultRouter()
router.register(r'games', VideoPokerGameViewSet)

urlpatterns = [path('', include(router.urls))]