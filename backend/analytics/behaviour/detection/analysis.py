from dataclasses import dataclass


@dataclass(frozen=True)
class DriverBehaviourAnalysis:
    """
    Behaviour analysis result for one telemetry observation.

    This represents what the driver was doing at a specific moment.
    It is not a trip summary or historical aggregate.
    """

    vehicle_id: str
    driver_id: str
    trip_id: str

    speeding: bool
    speed_excess_kmh: float

    harsh_braking: bool
    aggressive_throttle: bool
    high_rpm: bool

    severity: str
    odometer_km: float