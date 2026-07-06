"""
DriveVitals Dashboard Test Client

Connects to the Dashboard WebSocket and prints every
vehicle update received from the backend.
"""

import asyncio
import websockets


WS_URL = "ws://127.0.0.1:8000/ws/dashboard"


async def dashboard_client():

    async with websockets.connect(WS_URL) as websocket:

        print("🖥 Connected to Dashboard WebSocket\n")

        while True:

            message = await websocket.recv()

            print(message)


if __name__ == "__main__":
    asyncio.run(dashboard_client())