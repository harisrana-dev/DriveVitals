"""
Telemetry Sample model.

One time-stamped observation from a vehicle, shaped like data a real
OBD-II telemetry source could plausibly emit. This is the hand-off
point between the Fleet Runtime (which generates it) and DriveVitals
Analytics (which interprets it) — the sample itself carries no
interpretation, only measurements.

Immutable after creation (frozen dataclass) since a telemetry reading
is a historical fact once produced.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class TelemetrySample:
    timestamp: datetime
    vehicle_id: str
    driver_id: str
    trip_id: str

    speed_kmh: float
    rpm: float
    throttle_position_percent: float
    brake_pressure: float  # 0.0 (no braking) .. 1.0 (full braking)

    coolant_temperature_c: float
    engine_load_percent: float
    fuel_rate_lph: float
    fuel_level_percent: float

    odometer_km: float