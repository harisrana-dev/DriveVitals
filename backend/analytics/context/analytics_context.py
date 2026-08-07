"""
Analytics Context.

Immutable contextual reference information required to interpret
raw telemetry. A TelemetrySample tells us what the vehicle is doing;
an AnalyticsContext tells us what it *should* be doing — speed limits,
route type, vehicle specs, and the driver/trip association that
frames the analysis.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class AnalyticsContext:
    """Contextual facts that accompany telemetry for analysis."""

    vehicle_id: str
    driver_id: str
    trip_id: str

    route_id: str
    route_type: str
    speed_limit_kmh: float

    vehicle_make: str
    vehicle_model: str
    vehicle_year: int

    driver_name: str = ""
    route_name: str = ""
