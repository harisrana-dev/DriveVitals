from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class VehicleDashboardSummary:
    """
    Dashboard representation of one vehicle.

    This is NOT raw telemetry.
    It is a frontend-facing summary.
    """

    vehicle_id: str

    driver_id: str | None

    vehicle_name: str | None

    driver_name: str | None

    operational_status: str

    speed_kmh: float | None

    rpm: float | None

    throttle_position_percent: float | None

    brake_percent: float | None

    fuel_level_percent: float | None

    coolant_temperature_c: float | None

    engine_load_percent: float | None

    overall_health_score: float | None

    driver_safety_score: float

    driver_risk_level: str

    active_alert_count: int

    active_alert_text: str | None

    active_event_types: tuple[str, ...]

    speeding: bool

    aggressive_throttle: bool

    harsh_braking: bool

    high_rpm: bool

    odometer_km: float | None

    last_updated_at: datetime

    trip_status: str = "active"

    route_id: str | None = None

    route_name: str | None = None

    trip_started_at: datetime | None = None

    trip_distance_km: float | None = None

    fuel_rate_lph: float | None = None

    fuel_used_liters: float | None = None


@dataclass(frozen=True, slots=True)
class DashboardSnapshot:
    """
    Complete dashboard update payload.

    Represents the current fleet state
    required by the frontend.
    """

    timestamp: datetime

    total_fleet: int

    active_vehicle_count: int

    fleet_health_score: float

    attention_required: int

    vehicles: tuple[
        VehicleDashboardSummary,
        ...
    ]