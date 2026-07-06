"""
DriveVitals Dashboard WebSocket

Provides the live WebSocket endpoint used by frontend
dashboards.

Clients connecting to this endpoint automatically receive
live vehicle updates whenever the Vehicle State Manager
publishes new data.
"""

from fastapi import WebSocket, WebSocketDisconnect

from dashboard.connection_manager import dashboard_manager


async def dashboard_websocket(websocket: WebSocket):
    """
    Dashboard WebSocket endpoint.
    """

    await dashboard_manager.connect(websocket)

    try:
        while True:
            # Keep the connection alive.
            #
            # The dashboard doesn't need to send telemetry.
            # It only receives data.
            #
            # We simply wait for incoming messages (such as
            # heartbeat/ping messages from the frontend).
            await websocket.receive_text()

    except WebSocketDisconnect:

        dashboard_manager.disconnect(websocket)