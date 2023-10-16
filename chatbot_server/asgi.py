import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

from amend_data.routing import websocket_urlpatterns
from channels.routing import ChannelNameRouter
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "chatbot_server.settings")
django_asgi_app = get_asgi_application()

import amend_data.routing
from amend_data import consumers
application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AllowedHostsOriginValidator(
            AuthMiddlewareStack(URLRouter(websocket_urlpatterns))
        ),
        "channel": ChannelNameRouter({
            "response_person": consumers.ChatConsumer.as_asgi(),
            # "thumbnails-delete": consumers.DeleteConsumer.as_asgi(),
        }),
    }
)