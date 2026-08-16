from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import SicBoGameViewSet

router = DefaultRouter()
router.register(r'games', SicBoGameViewSet)

urlpatterns = [
    path('', include(router.urls)),
]