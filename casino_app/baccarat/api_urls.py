from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import BaccaratGameViewSet

router = DefaultRouter()
router.register(r'games', BaccaratGameViewSet)

urlpatterns = [
    path('', include(router.urls)),
]