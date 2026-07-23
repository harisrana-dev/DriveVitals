from fastapi import FastAPI
from api.telemetry_routes import router as telemetry_router
from websocket.ws_server import websocket_endpoint, processor_worker
from api.state_routes import router as state_router
from dashboard.websocket import dashboard_websocket
import asyncio

app = FastAPI(
    title="DriveVitals Backend TEST"
)

print("✅ MAIN.PY IS LOADED")
# HTTP routes
app.include_router(telemetry_router, prefix="/api")

# Telemetry Websocket
app.websocket("/ws/telemetry")(websocket_endpoint)

# Dashboard WebSocket
app.websocket("/ws/dashboard")(dashboard_websocket)

# State API route
app.include_router(state_router, prefix="/api")

print(app.routes)


@app.on_event("startup")
async def startup():
    asyncio.create_task(processor_worker())