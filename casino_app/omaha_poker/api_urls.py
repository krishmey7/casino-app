from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import OmahaPokerGameViewSet

router = DefaultRouter()
router.register(r'games', OmahaPokerGameViewSet)

urlpatterns = [path('', include(router.urls))]