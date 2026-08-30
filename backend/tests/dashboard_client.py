"""
DriveVitals Dashboard Test Client

Connects to the Dashboard WebSocket and prints every
vehicle update received from the backend.
"""

import asyncio
import os
import websockets


def _url() -> str:
    token = os.environ.get("DRIVEVITALS_TOKEN")
    if not token:
        raise SystemExit(
            "DRIVEVITALS_TOKEN is required: the dashboard WebSocket now "
            "rejects anonymous connections. Log in via POST /api/v1/auth/login "
            "and export the returned token as DRIVEVITALS_TOKEN."
        )
    return f"ws://127.0.0.1:8000/ws/dashboard?token={token}"


async def dashboard_client():

    async with websockets.connect(_url()) as websocket:

        print("Connected to Dashboard WebSocket\n")

        while True:

            message = await websocket.recv()

            print(message)


if __name__ == "__main__":
    asyncio.run(dashboard_client())