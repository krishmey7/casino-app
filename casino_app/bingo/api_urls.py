from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import BingoGameViewSet

router = DefaultRouter()
router.register(r'games', BingoGameViewSet)

urlpatterns = [
    path('', include(router.urls)),
]