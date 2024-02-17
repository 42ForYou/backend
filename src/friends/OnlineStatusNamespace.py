import socketio
from asgiref.sync import sync_to_async
from socketcontrol.events import sio
from socketcontrol.events import get_user_by_token


@sync_to_async
def update_online_sid(user, sid):
    user.socket_session.online_session_id = sid
    user.socket_session.save()


class OnlineStatusNamespace(socketio.AsyncNamespace):
    def __init__(self, namespace="/online_status"):
        super().__init__(namespace=namespace)

    # SIO: F>B connect
    async def on_connect(self, sid, environ):
        try:
            cookies = environ.get("HTTP_COOKIE", "")
            cookie_dict = dict(
                item.split("=") for item in cookies.split("; ") if "=" in item
            )
            token = cookie_dict.get("kimyeonhkimbabo_token", None)
            if token:
                user = await get_user_by_token(token)
                await update_online_sid(user, sid)
            else:
                print("No token")
                await self.disconnect(sid)
        except Exception as e:
            print(f"Error in connect: {e}")
            await self.disconnect(sid)
