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

    brake_pressure: float | None

    fuel_level_percent: float | None

    coolant_temperature_c: float | None

    engine_load_percent: float | None

    overall_health_score: float | None

    active_alert_count: int

    active_alert_text: str | None

    active_event_types: tuple[str, ...]

    speeding: bool

    aggressive_throttle: bool

    harsh_braking: bool

    high_rpm: bool

    odometer_km: float | None

    last_updated_at: datetime


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