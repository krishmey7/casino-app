from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import RedDogGameViewSet

router = DefaultRouter()
router.register(r'games', RedDogGameViewSet)

urlpatterns = [path('', include(router.urls))]