from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/ludo/(?P<game_id>[^/]+)/$', consumers.LudoGameConsumer.as_asgi()),
]
