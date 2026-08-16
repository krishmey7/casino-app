from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import PaiGowGameViewSet

router = DefaultRouter()
router.register(r'games', PaiGowGameViewSet)

urlpatterns = [
    path('', include(router.urls)),
]