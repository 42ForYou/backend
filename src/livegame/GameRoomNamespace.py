import socketio


def emit_update_room():
    pass


def emit_destroyed():
    pass


def emit_update_tournament():
    pass


class GameRoomNamespace(socketio.Namespace):
    def on_connect(self, sid, environ):
        pass

    def on_disconnect(self, sid):
        pass

    def on_exited(self, sid, data):
        # self.emit("my_response", data)
        pass

    def on_start(self, sid, data):
        # self.emit("my_response", data)
        pass
