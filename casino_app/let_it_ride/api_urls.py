from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import LetItRideGameViewSet

router = DefaultRouter()
router.register(r'games', LetItRideGameViewSet)

urlpatterns = [path('', include(router.urls))]