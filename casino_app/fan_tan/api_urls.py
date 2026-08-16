from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import FanTanGameViewSet

router = DefaultRouter()
router.register(r'games', FanTanGameViewSet)

urlpatterns = [path('', include(router.urls))]