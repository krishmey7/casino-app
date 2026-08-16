from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import BlackjackGameViewSet

router = DefaultRouter()
router.register(r'games', BlackjackGameViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
