import asyncio
import websockets
import json
from simulator.car_in_city import OBDVehicleSimulator


WS_URL = "ws://127.0.0.1:8000/ws/telemetry"


async def stream_to_backend():
    sim = OBDVehicleSimulator(update_hz=1)

    async with websockets.connect(WS_URL) as websocket:
        print("✅ Connected to FastAPI WebSocket")

        for telemetry in sim.stream():
            data = telemetry.to_dict()

            await websocket.send(json.dumps(data))
            print("📤 Sent:", data)

            await asyncio.sleep(sim.dt)


if __name__ == "__main__":
    asyncio.run(stream_to_backend())