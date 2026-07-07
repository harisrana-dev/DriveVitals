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
        Broadcast a vehicle update to every connected dashboard.
        """


        if not self.active_connections:
            return

        disconnected = []

        for websocket in self.active_connections:

            try:
                vehicle = data.get("vehicle", {})
                vehicle_id = vehicle.get("vehicle_id", "UNKNOWN")

                print(f"➡️ Sending update for {vehicle_id}")

                await websocket.send_json(data)

                print(f"✅ Successfully sent {vehicle_id}")

            except Exception as e:

                print("❌ Broadcast Exception:")
                print(repr(e))

                disconnected.append(websocket)

        for websocket in disconnected:
            self.disconnect(websocket)


# ------------------------------------------------------
# Global singleton
# ------------------------------------------------------

dashboard_manager = DashboardConnectionManager()