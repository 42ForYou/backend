import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pong.settings")

import django

django.setup()

import socketio
import asyncio
from django.core.asgi import get_asgi_application
from socketcontrol.events import sio
from livegame.GameSessionRegistry import update_game_session_registry_forever


django_asgi_app = get_asgi_application()


async def on_startup():
    asyncio.create_task(update_game_session_registry_forever())


socketio_app = socketio.ASGIApp(sio, django_asgi_app, on_startup=on_startup)

application = socketio_app
