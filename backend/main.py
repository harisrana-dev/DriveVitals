from fastapi import FastAPI
from api.telemetry_routes import router as telemetry_router
from websocket.ws_server import websocket_endpoint, processor_worker
import asyncio

app = FastAPI()

# HTTP routes
app.include_router(telemetry_router, prefix="/api")

# WebSocket route
app.websocket("/ws/telemetry")(websocket_endpoint)


@app.on_event("startup")
async def startup():
    asyncio.create_task(processor_worker())