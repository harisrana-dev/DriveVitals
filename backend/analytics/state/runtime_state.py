"""
Runtime Analytics State.

Represents the latest known live telemetry snapshot for a single
vehicle/driver/trip combination. Updated by the runtime analyzer on
each incoming TelemetrySample — this is a mutable mirror of the
most recent reading, not a historical aggregate.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class RuntimeAnalyticsState:
    vehicle_id: str
    driver_id: str
    trip_id: str

    timestamp: datetime

    speed_kmh: float
    rpm: float
    throttle_position_percent: float
    brake_pressure: float

    coolant_temperature_c: float
    engine_load_percent: float
    fuel_rate_lph: float
    fuel_level_percent: float

    odometer_km: float
