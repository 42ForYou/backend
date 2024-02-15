import os
import socketio

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pong.settings")

import django

django.setup()

from django.core.asgi import get_asgi_application

from socketcontrol.events import register_sio_control
from livechat.events import register_sio_chat
from livegame.events import register_sio_game


django_asgi_app = get_asgi_application()


async def on_startup():
    asyncio.create_task(update_game_session_registry_forever())


socketio_app = socketio.ASGIApp(sio, django_asgi_app, on_startup=on_startup)

application = socketio_app
