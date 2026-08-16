from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import CasinoWarGameViewSet

router = DefaultRouter()
router.register(r'games', CasinoWarGameViewSet)

urlpatterns = [path('', include(router.urls))]