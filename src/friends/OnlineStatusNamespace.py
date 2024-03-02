import logging

import socketio
from asgiref.sync import sync_to_async

from socketcontrol.events import get_user_by_token


@sync_to_async
def update_online_sid(user, sid):
    user.socket_session.online_session_id = sid
    user.socket_session.save()


class OnlineStatusNamespace(socketio.AsyncNamespace):
    def __init__(self, namespace="/online_status"):
        super().__init__(namespace=namespace)
        self.logger = logging.getLogger(f"{__package__}.{__class__.__name__}")

    # SIO: F>B connect
    async def on_connect(self, sid, environ):
        self.logger.debug(f"connect from sid {sid}")
        try:
            cookies = environ.get("HTTP_COOKIE", "")
            cookie_dict = dict(
                item.split("=") for item in cookies.split("; ") if "=" in item
            )
            token = cookie_dict.get("pong_token", None)
            if token:
                user = await get_user_by_token(token)
                await update_online_sid(user, sid)
            else:
                self.logger.warn("No token")
                await self.disconnect(sid)
        except Exception as e:
            self.logger.error(f"Error in connect: {e}")
            await self.disconnect(sid)
