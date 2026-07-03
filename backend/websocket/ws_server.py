from fastapi import WebSocket, WebSocketDisconnect
import json
import asyncio

from telemetry.dispatcher import TelemetryDispatcher

dispatcher = TelemetryDispatcher()

queue = asyncio.Queue()


from fastapi import WebSocket, WebSocketDisconnect
import json
import asyncio

from telemetry.dispatcher import TelemetryDispatcher

dispatcher = TelemetryDispatcher()

queue = asyncio.Queue()


async def processor_worker():
    while True:
        packet = await queue.get()
        dispatcher.dispatch(packet)
        print("QUEUE GET:", id(queue))


async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    print("🔌 Connected")

    try:
        while True:
            data = await websocket.receive_text()

            packet = json.loads(data)

            # DO NOT process here
            print("QUEUE PUT:", id(queue))
            await queue.put(packet)

    except WebSocketDisconnect:
        print("❌ Disconnected")


async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("🔌 Connected")

    try:
        while True:
            data = await websocket.receive_text()
            packet = json.loads(data)

            print("📤 QUEUE PUT:", packet["vehicle_id"] if "vehicle_id" in packet else packet)

            await queue.put(packet)

    except WebSocketDisconnect:
        print("❌ Disconnected")