import socketio


class SubGameNamespace(socketio.AsyncNamespace):
    def on_connect(self, sid, environ):
        print(f"Ns={self.namespace}, {sid} connected")
        # TODO: 접속한 유저가 대진표에서 어디에 있는지 파악 등,,,

    def on_disconnect(self, sid):
        print(f"Ns={self.namespace}, {sid} disconnected")
        # TODO: 나간 유저가 대진표에서 어디에 있는지 파악 등,,,

    def on_leave(self, sid, data):
        print(f"Ns={self.namespace}, {sid} event: leave, data={data}")
        # TODO: Impl

    def on_keyboard_input(self, sid, data):
        print(f"Ns={self.namespace}, {sid} event: keyboard_input, data={data}")
        # TODO: Impl
