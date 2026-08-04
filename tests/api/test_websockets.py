from starlette.testclient import TestClient

from backend.api.main import app


class TestWebSockets:

    def test_dashboard_websocket_connects(self) -> None:
        client = TestClient(app)

        with client.websocket_connect("/ws/dashboard") as websocket:
            websocket.send_text("ping")

    def test_trips_websocket_connects(self) -> None:
        client = TestClient(app)

        with client.websocket_connect("/ws/trips") as websocket:
            websocket.send_text("ping")
