from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from api.telemetry_routes import router as telemetry_router

app = FastAPI()
app.include_router(telemetry_router, prefix="/api")


# store active connections (for future dashboard use)
active_connections = []

@app.websocket("/ws/telemetry")
async def telemetry_ws(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)

    try:
        while True:
            data = await websocket.receive_json()
            print("📡 LIVE TELEMETRY:", data)

            # optional: broadcast to all connected dashboards later
            for conn in active_connections:
                await conn.send_json(data)

    except WebSocketDisconnect:
        print("❌ Client disconnected")
        active_connections.remove(websocket)