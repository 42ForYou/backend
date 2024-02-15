import socketio


class SubGameNamespace(socketio.Namespace):
    def on_connect(self, sid, environ):
        pass

    def on_disconnect(self, sid):
        pass

    def on_start(self, sid, data):
        # self.emit("my_response", data)
        pass

    def on_update_time_left(self, sid, data):
        # self.emit("my_response", data)
        pass

    def on_ended(self, sid, data):
        # self.emit("my_response", data)
        pass

    def on_leave(self, sid, data):
        # self.emit("my_response", data)
        pass

    def on_update_scores(self, sid, data):
        # self.emit("my_response", data)
        pass

    def on_update_track_ball(self, sid, data):
        # self.emit("my_response", data)
        pass

    def on_keyboard_input(self, sid, data):
        # self.emit("my_response", data)
        pass

    def on_update_track_paddle(self, sid, data):
        # self.emit("my_response", data)
        pass
