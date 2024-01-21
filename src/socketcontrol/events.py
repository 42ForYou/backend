import socketio

"""
connect, disconnect 에 액세스할 수 없음 에러는 문제없다.
이벤트를 등록하면 자동으로 connect, disconnect 가 등록된다.
connect, disconnect 는 socketio 라이브러리에서 자동으로 등록된다.
"""


def register_sio_control(sio):
    @sio.on("connect")
    async def connect(sid: str, environ: dict) -> None:
        print("Client connected", sid)

    @sio.on("disconnect")
    async def disconnect(sid):
        print("Client disconnected", sid)
