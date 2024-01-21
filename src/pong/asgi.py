import os
import django
from django.core.asgi import get_asgi_application
import socketio
from socketcontrol.events import register_sio_control
from livechat.events import register_sio_chat
from livegame.events import register_sio_game

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pong.settings")
django.setup()

django_asgi_app = get_asgi_application()
sio = socketio.AsyncServer(async_mode="asgi")

register_sio_control(sio)
register_sio_chat(sio)
register_sio_game(sio)

socketio_app = socketio.ASGIApp(sio, django_asgi_app)


application = socketio_app
