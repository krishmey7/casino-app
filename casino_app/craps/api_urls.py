from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import CrapsGameViewSet

router = DefaultRouter()
router.register(r'games', CrapsGameViewSet)

urlpatterns = [
    path('', include(router.urls)),
]