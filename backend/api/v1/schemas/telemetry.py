from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TelemetryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sample_id: str
    trip_id: str
    vehicle_id: str
    timestamp: datetime
    speed_kmh: float
    rpm: float
    engine_load_percent: float
    throttle_percent: float
    brake_percent: float
    fuel_rate_lph: float
    fuel_level_percent: float
    coolant_temperature_c: float
    odometer_km: float
