from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import ScratchCardGameViewSet

router = DefaultRouter()
router.register(r'games', ScratchCardGameViewSet)

urlpatterns = [path('', include(router.urls))]