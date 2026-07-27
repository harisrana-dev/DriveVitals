from fastapi import WebSocket


class WebSocketManager:
    """
    Manages active WebSocket connections.

    Responsible for:
        - accepting connections
        - removing disconnected clients
        - broadcasting messages
    """

    def __init__(self) -> None:
        self._connections: list[
            WebSocket
        ] = []

    async def connect(
        self,
        websocket: WebSocket,
    ) -> None:
        await websocket.accept()

        self._connections.append(
            websocket
        )

    def disconnect(
        self,
        websocket: WebSocket,
    ) -> None:
        if websocket in self._connections:
            self._connections.remove(
                websocket
            )

    async def broadcast(
        self,
        message: dict,
    ) -> None:
        disconnected: list[
            WebSocket
        ] = []

        for websocket in self._connections:

            try:

                await websocket.send_json(
                    message
                )

            except Exception:

                disconnected.append(
                    websocket
                )

        for websocket in disconnected:

            self.disconnect(
                websocket
            )

    @property
    def connection_count(
        self,
    ) -> int:
        return len(
            self._connections
        )