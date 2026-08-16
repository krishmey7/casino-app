from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import KenoGameViewSet

router = DefaultRouter()
router.register(r'games', KenoGameViewSet)

urlpatterns = [
    path('', include(router.urls)),
]