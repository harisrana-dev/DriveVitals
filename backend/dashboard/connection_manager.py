"""
DriveVitals Dashboard Connection Manager

Maintains all active dashboard WebSocket connections.

This component is responsible for:

- Registering dashboard clients
- Removing disconnected clients
- Broadcasting live vehicle updates

It does NOT perform analytics or telemetry processing.
It only manages dashboard connections.
"""

import json
from fastapi import WebSocket


class DashboardConnectionManager:

    def __init__(self):
        # All currently connected dashboard clients
        self.active_connections: list[WebSocket] = []

    # --------------------------------------------------

    async def connect(self, websocket: WebSocket):
        """
        Accept a new dashboard connection.
        """
        await websocket.accept()

        self.active_connections.append(websocket)

        print(
            f"🖥 Dashboard connected "
            f"({len(self.active_connections)} clients)"
        )

    # --------------------------------------------------

    def disconnect(self, websocket: WebSocket):
        """
        Remove a disconnected dashboard.
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

        print(
            f"❌ Dashboard disconnected "
            f"({len(self.active_connections)} clients)"
        )

    # --------------------------------------------------

    async def broadcast(self, data):
        """
        Broadcast a JSON message to every dashboard.
        """

        if not self.active_connections:
            return


        disconnected = []

        for websocket in self.active_connections:

            try:
                await websocket.send_json(data)

            except Exception:
                disconnected.append(websocket)

        # Clean up dead connections
        for websocket in disconnected:
            self.disconnect(websocket)


# ------------------------------------------------------
# Global singleton
# ------------------------------------------------------

dashboard_manager = DashboardConnectionManager()