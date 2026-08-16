from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import SlotsGameViewSet

router = DefaultRouter()
router.register(r'games', SlotsGameViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
