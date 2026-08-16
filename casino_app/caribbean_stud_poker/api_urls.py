from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import CaribbeanStudPokerGameViewSet

router = DefaultRouter()
router.register(r'games', CaribbeanStudPokerGameViewSet)

urlpatterns = [path('', include(router.urls))]