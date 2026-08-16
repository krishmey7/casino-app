from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import MinesGameViewSet

router = DefaultRouter()
router.register(r'games', MinesGameViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
