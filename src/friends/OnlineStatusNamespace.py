import socketio
from socketcontrol.events import sio


class OnlineStatusNamespace(socketio.AsyncNamespace):
    def __init__(self, namespace="/online_status"):
        super().__init__(namespace=namespace)
