from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import DoubleExposureBlackjackGameViewSet

router = DefaultRouter()
router.register(r'games', DoubleExposureBlackjackGameViewSet)

urlpatterns = [path('', include(router.urls))]