from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import Spanish21GameViewSet

router = DefaultRouter()
router.register(r'games', Spanish21GameViewSet)

urlpatterns = [path('', include(router.urls))]