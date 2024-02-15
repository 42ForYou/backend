import os
import django
from django.core.asgi import get_asgi_application
import socketio
from socketcontrol.events import sio
from livegame.GameSessionRegistry import update_game_session_registry_forever

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pong.settings")
django.setup()

django_asgi_app = get_asgi_application()

socketio_app = socketio.ASGIApp(
    sio, django_asgi_app, on_startup=update_game_session_registry_forever()
)

application = socketio_app
