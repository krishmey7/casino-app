from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/face_ou_pile/(?P<game_id>[^/]+)/$', consumers.FaceOuPileGameConsumer.as_asgi()),
]
