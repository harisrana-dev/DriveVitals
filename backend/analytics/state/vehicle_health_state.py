"""
Vehicle Health State.

Represents the current mechanical health assessment of a vehicle.
Updated by the vehicle health analyzer; carries status, scores, and
accumulated abnormal-event counts. Contains no health-calculation or
rule logic.
"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class VehicleHealthState:
    vehicle_id: str

    health_status: str = ""
    health_score: float = 0.0

    coolant_temperature_c: float = 0.0
    engine_load_percent: float = 0.0
    rpm: float = 0.0

    overheating_risk: str = ""
    engine_stress_level: str = ""

    estimated_fuel_efficiency_km_per_liter: float = 0.0

    abnormal_temperature_events: int = 0
    high_load_events: int = 0
    high_rpm_events: int = 0

    health_reasons: list[str] = field(default_factory=list)

    last_updated: datetime | None = None
