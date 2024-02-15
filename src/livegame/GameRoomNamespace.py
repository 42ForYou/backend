import socketio


class GameRoomNamespace(socketio.Namespace):
    def on_connect(self, sid, environ):
        pass

    def on_disconnect(self, sid):
        pass

    def on_exited(self, sid, data):
        # self.emit("my_response", data)
        pass

    def on_update_room(self, sid, data):
        # self.emit("my_response", data)
        pass

    def on_destroyed(self, sid, data):
        # self.emit("my_response", data)
        pass

    def on_start(self, sid, data):
        # self.emit("my_response", data)
        pass

    def on_update_tournament(self, sid, data):
        # self.emit("my_response", data)
        pass
