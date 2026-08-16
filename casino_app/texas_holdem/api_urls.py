from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import TexasHoldemGameViewSet

router = DefaultRouter()
router.register(r'games', TexasHoldemGameViewSet)

urlpatterns = [path('', include(router.urls))]