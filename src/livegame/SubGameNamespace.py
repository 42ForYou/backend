import socketio


class SubGameNamespace(socketio.AsyncNamespace):
    # SIO: F>B connect
    def on_connect(self, sid, environ):
        print(f"Ns={self.namespace}, {sid} connected")
        # TODO: 접속한 유저가 대진표에서 어디에 있는지 파악 등,,,

    # SIO: F>B disconnect
    def on_disconnect(self, sid):
        print(f"Ns={self.namespace}, {sid} disconnected")
        # TODO: 나간 유저가 대진표에서 어디에 있는지 파악 등,,,

    # SIO: F>B leave
    async def on_leave(self, sid, data):
        print(f"Ns={self.namespace}, {sid} event: leave, data={data}")
        # TODO: Impl

    # SIO: F>B keyboard_input
    async def on_keyboard_input(self, sid, data):
        print(f"Ns={self.namespace}, {sid} event: keyboard_input, data={data}")
        # TODO: Impl
