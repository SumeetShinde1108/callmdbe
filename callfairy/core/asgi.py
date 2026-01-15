"""
ASGI config for callfairy project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'callfairy.core.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    # We'll add WebSocket routing later
    # "websocket": AuthMiddlewareStack(
    #     URLRouter([
    #         # Add WebSocket routes here
    #     ])
    # ),
})
