import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

http_response_app = get_asgi_application()

# Import wsPattern lazily to ensure Django's app registry is ready
def get_websocket_application():
    from chat.routing import wsPattern
    return URLRouter(wsPattern)

application = ProtocolTypeRouter(
    {"http": http_response_app, "websocket": get_websocket_application()}
)
