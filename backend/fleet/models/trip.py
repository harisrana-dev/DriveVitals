"""
Trip model.

Represents an actual operational journey undertaken by a
vehicle/driver pair along a route. Tracks a simple lifecycle:

    ASSIGNED -> STARTED -> IN_PROGRESS -> COMPLETED

Completion is determined by route progress: once distance travelled
during the trip reaches (or exceeds) the route's distance, the
destination has been reached.

This is a small, explicit state machine — not a general lifecycle
framework.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class TripStatus(str, Enum):
    ASSIGNED = "assigned"
    STARTED = "started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


@dataclass
class Trip:
    trip_id: str
    vehicle_id: str
    driver_id: str
    route_id: str

    status: TripStatus = TripStatus.ASSIGNED
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    starting_odometer_km: float = 0.0
    ending_odometer_km: Optional[float] = None

    # Distance covered so far during this trip (not the vehicle's
    # lifetime odometer — see RuntimeState for the distinction).
    distance_travelled_km: float = field(default=0.0)

    def start(self, starting_odometer_km: float, at: Optional[datetime] = None) -> None:
        if self.status != TripStatus.ASSIGNED:
            raise ValueError(f"Cannot start a trip in status {self.status}")
        self.starting_odometer_km = starting_odometer_km
        self.started_at = at or datetime.utcnow()
        self.status = TripStatus.STARTED

    def advance(self, delta_km: float) -> None:
        """Record additional distance travelled during the trip."""
        if self.status not in (TripStatus.STARTED, TripStatus.IN_PROGRESS):
            raise ValueError(f"Cannot advance a trip in status {self.status}")
        if delta_km < 0:
            raise ValueError("Distance travelled cannot decrease")
        self.distance_travelled_km += delta_km
        if self.status == TripStatus.STARTED:
            self.status = TripStatus.IN_PROGRESS

    def is_complete(self, route_distance_km: float) -> bool:
        return self.distance_travelled_km >= route_distance_km

    def complete(self, ending_odometer_km: float, at: Optional[datetime] = None) -> None:
        if self.status != TripStatus.IN_PROGRESS:
            raise ValueError(f"Cannot complete a trip in status {self.status}")
        self.ending_odometer_km = ending_odometer_km
        self.completed_at = at or datetime.utcnow()
        self.status = TripStatus.COMPLETED