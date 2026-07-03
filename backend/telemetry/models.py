"""
DriveVitals Telemetry Model

Defines the canonical telemetry packet used throughout
the backend. Every telemetry source (simulator or future
OBD-II device) must conform to this model.
"""

from pydantic import BaseModel
from datetime import datetime


class TelemetryPacket(BaseModel):
    # ----------------------------
    # Metadata
    # ----------------------------

    timestamp: datetime

    vehicle_id: str
    driver_id: str
    fleet_id: str
    vehicle_type: str

    # ----------------------------
    # Driving State
    # ----------------------------

    speed_kmh: float
    rpm: int
    gear: int
    phase: str

    # ----------------------------
    # Engine Parameters
    # ----------------------------

    throttle_position: float
    engine_load: float
    coolant_temperature: float
    fuel_rate_lph: float

    class Config:
        extra = "ignore"