import socketio


def emit_start():
    pass


def emit_update_time_left():
    pass


def emit_ended():
    pass


def emit_update_scores():
    pass


def emit_update_track_ball():
    pass


def emit_update_track_paddle():
    pass


class SubGameNamespace(socketio.Namespace):
    def on_connect(self, sid, environ):
        pass

    def on_disconnect(self, sid):
        pass

    def on_leave(self, sid, data):
        # self.emit("my_response", data)
        pass

    def on_keyboard_input(self, sid, data):
        # self.emit("my_response", data)
        pass
