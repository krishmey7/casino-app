"""
ASGI config for projet_casino project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projet_casino.settings')

# Initialize Django
django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            # Lazy import to avoid Apps aren't loaded yet error
            __import__('casino_app.checkers.routing', fromlist=['websocket_urlpatterns']).websocket_urlpatterns +
            __import__('casino_app.ludo.routing', fromlist=['websocket_urlpatterns']).websocket_urlpatterns +
            __import__('casino_app.face_ou_pile.routing', fromlist=['websocket_urlpatterns']).websocket_urlpatterns
        )
    ),
})
