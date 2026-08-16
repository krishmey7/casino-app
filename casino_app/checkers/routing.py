from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/checkers/(?P<game_id>[^/]+)/$', consumers.CheckersGameConsumer.as_asgi()),
]
