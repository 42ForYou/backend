import os
import socketio

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pong.settings")

import django

django.setup()

from django.core.asgi import get_asgi_application
from socketcontrol.events import sio
from friends.OnlineStatusNamespace import OnlineStatusNamespace


django_asgi_app = get_asgi_application()


socketio_app = socketio.ASGIApp(sio, django_asgi_app)

sio.register_namespace(OnlineStatusNamespace())

application = socketio_app
