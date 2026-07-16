"""Trip entity: domain data describing a single trip.

Pure data model -- no route calculation, no fuel simulation, no
scoring logic. Completed trips are never deleted; a Trip instance is a
permanent historical record once its status reaches a terminal state
(COMPLETED or CANCELLED), which future sprints' Fleet/Analytics layers
are expected to retain indefinitely.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from digital_twin.common.enums import TripStatus
from digital_twin.common.exceptions import ConfigurationError


class TripEventType(str, Enum):
    """Category of a discrete event recorded during a trip."""

    DEPARTED = "DEPARTED"
    ARRIVED = "ARRIVED"
    DELAYED = "DELAYED"
    REROUTED = "REROUTED"
    INCIDENT = "INCIDENT"
    CARGO_LOADED = "CARGO_LOADED"
    CARGO_UNLOADED = "CARGO_UNLOADED"
    BREAK_STARTED = "BREAK_STARTED"
    BREAK_ENDED = "BREAK_ENDED"


@dataclass(frozen=True)
class TripEvent:
    """A single discrete event that occurred during a trip.

    Attributes:
        event_type: Category of the event.
        timestamp: Simulated time the event occurred.
        description: Free-form human-readable detail about the event.
    """

    event_type: TripEventType
    timestamp: datetime
    description: str = ""


@dataclass(frozen=True)
class TripStatusChange:
    """A single status transition recorded in a trip's history.

    Attributes:
        status: The status transitioned into.
        timestamp: Simulated time of the transition.
    """

    status: TripStatus
    timestamp: datetime


@dataclass
class Trip:
    """A single trip: its plan, its progress, and its permanent record.

    Attributes:
        trip_id: Unique identifier for the trip.
        vehicle_id: Id of the assigned vehicle, if any.
        driver_id: Id of the assigned driver, if any.
        route_id: Id of the assigned route, if any.
        cargo_id: Id of the assigned cargo, if any.
        start_time: Simulated time the trip started, if started.
        end_time: Simulated time the trip ended, if ended.
        distance_planned_km: Planned distance for the trip.
        distance_completed_km: Distance actually covered so far.
        duration_minutes: Actual elapsed duration, once known.
        average_speed_kmh: Average speed over the trip so far.
        fuel_consumed_liters: Fuel/energy consumed so far.
        fuel_efficiency_km_per_liter: Distance covered per unit of fuel.
        driver_score: Driver performance score for this trip, 0-100.
        vehicle_score: Vehicle performance score for this trip, 0-100.
        events: Chronological log of discrete events during the trip.
        status: Current lifecycle status of the trip.
        status_history: Chronological log of status transitions,
            forming the trip's permanent audit trail.
    """

    trip_id: str
    vehicle_id: str | None = None
    driver_id: str | None = None
    route_id: str | None = None
    cargo_id: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    distance_planned_km: float = 0.0
    distance_completed_km: float = 0.0
    duration_minutes: float = 0.0
    average_speed_kmh: float = 0.0
    fuel_consumed_liters: float = 0.0
    fuel_efficiency_km_per_liter: float = 0.0
    driver_score: float = 100.0
    vehicle_score: float = 100.0
    events: list[TripEvent] = field(default_factory=list)
    status: TripStatus = TripStatus.PENDING
    status_history: list[TripStatusChange] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate non-negative distances/consumption and bounded scores.

        Raises:
            ConfigurationError: If a distance/fuel/duration value is
                negative, or a score is outside [0.0, 100.0].
        """
        for non_negative_field in (
            "distance_planned_km",
            "distance_completed_km",
            "duration_minutes",
            "average_speed_kmh",
            "fuel_consumed_liters",
        ):
            if getattr(self, non_negative_field) < 0:
                raise ConfigurationError(f"{non_negative_field} cannot be negative.")
        for score_field in ("driver_score", "vehicle_score"):
            value = getattr(self, score_field)
            if not (0.0 <= value <= 100.0):
                raise ConfigurationError(f"{score_field} must be between 0.0 and 100.0.")