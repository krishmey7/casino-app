from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import PontoonGameViewSet

router = DefaultRouter()
router.register(r'games', PontoonGameViewSet)

urlpatterns = [path('', include(router.urls))]