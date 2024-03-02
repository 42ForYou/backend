import socketio

from django.test import TestCase


class SocketIOTestCase(TestCase):
    def setUp(self):
        self.sio = socketio.Client()

    def test_connect_and_disconnect(self):
        @self.sio.event
        def connect():
            print("I'm connected!")

        @self.sio.event
        def disconnect():
            print("I'm disconnected!")

        self.sio.connect("http://localhost:8000")
        self.assertTrue(self.sio.connected)  # 연결이 성공했는지 확인
        self.sio.disconnect()
        self.assertFalse(self.sio.connected)  # 연결이 종료되었는지 확인
