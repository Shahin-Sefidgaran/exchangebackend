from starlette.testclient import TestClient

from main import app


def test_pong_ws():
    client = TestClient(app=app)
    with client.websocket_connect("/ws/ping/1") as websocket:
        message = websocket.receive_text()
        assert message == 'pong'
