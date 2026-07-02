from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

class TelemetryIn(BaseModel):
    timestamp: str
    rpm: int
    speed_kmh: float
    throttle_position: float
    engine_load: float
    coolant_temperature: float
    fuel_rate_lph: float
    gear: int
    phase: str

@router.post("/telemetry")
def receive_telemetry(data: TelemetryIn):
    print("📡 TELEMETRY RECEIVED:", data.dict())

    return {
        "status": "ok",
        "received_at": datetime.now().isoformat()
    }