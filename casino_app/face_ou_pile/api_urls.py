from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import FaceOuPileGameViewSet

router = DefaultRouter()
router.register(r'games', FaceOuPileGameViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
