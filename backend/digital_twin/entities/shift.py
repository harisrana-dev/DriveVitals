"""Shift entity: domain data describing a scheduled driver work period.

Pure data model -- no scheduling logic, no fatigue calculation. Those
belong to future sprints; this entity only stores the resulting values
(e.g. `fatigue_metrics`), not how they were derived.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from digital_twin.common.exceptions import ConfigurationError


class ShiftStatus(str, Enum):
    """Lifecycle status of a shift."""

    SCHEDULED = "SCHEDULED"
    ACTIVE = "ACTIVE"
    ON_BREAK = "ON_BREAK"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


@dataclass
class Break:
    """A single rest break taken during a shift.

    Attributes:
        start_time: Simulated time the break started.
        end_time: Simulated time the break ended, if it has ended.
        duration_minutes: Planned or actual break duration, in minutes.
    """

    start_time: datetime
    end_time: datetime | None = None
    duration_minutes: float = 0.0

    def __post_init__(self) -> None:
        """Validate the break's duration is non-negative.

        Raises:
            ConfigurationError: If duration_minutes is negative.
        """
        if self.duration_minutes < 0:
            raise ConfigurationError("Break duration_minutes cannot be negative.")


@dataclass
class FatigueMetrics:
    """Aggregated fatigue-related measurements for a shift.

    Attributes:
        continuous_work_hours: Hours worked continuously since the
            last break.
        total_break_minutes: Total break time taken this shift.
        fatigue_score: Overall fatigue score for the shift, on a 0.0
            (fully rested) to 1.0 (fully fatigued) scale.
    """

    continuous_work_hours: float = 0.0
    total_break_minutes: float = 0.0
    fatigue_score: float = 0.0

    def __post_init__(self) -> None:
        """Validate fatigue_score is within its defined range.

        Raises:
            ConfigurationError: If fatigue_score is outside [0.0, 1.0],
                or any accumulated value is negative.
        """
        if not (0.0 <= self.fatigue_score <= 1.0):
            raise ConfigurationError("fatigue_score must be between 0.0 and 1.0.")
        if self.continuous_work_hours < 0:
            raise ConfigurationError("continuous_work_hours cannot be negative.")
        if self.total_break_minutes < 0:
            raise ConfigurationError("total_break_minutes cannot be negative.")


@dataclass
class Shift:
    """A single scheduled work period for a driver/vehicle pairing.

    Attributes:
        shift_id: Unique identifier for the shift.
        driver_id: Id of the driver this shift belongs to.
        vehicle_id: Id of the vehicle assigned for this shift, if any.
        shift_start: Simulated time the shift is scheduled to start.
        shift_end: Simulated time the shift is scheduled to end.
        breaks: Rest breaks taken during the shift.
        working_time_minutes: Cumulative active working time this shift.
        rest_time_minutes: Cumulative rest time this shift.
        completed_trip_ids: Ids of trips completed during this shift.
        status: Current lifecycle status of the shift.
        fatigue_metrics: Aggregated fatigue measurements for this shift.
    """

    shift_id: str
    driver_id: str
    vehicle_id: str | None
    shift_start: datetime
    shift_end: datetime
    breaks: list[Break] = field(default_factory=list)
    working_time_minutes: float = 0.0
    rest_time_minutes: float = 0.0
    completed_trip_ids: list[str] = field(default_factory=list)
    status: ShiftStatus = ShiftStatus.SCHEDULED
    fatigue_metrics: FatigueMetrics = field(default_factory=FatigueMetrics)

    def __post_init__(self) -> None:
        """Validate shift timing and cumulative values.

        Raises:
            ConfigurationError: If shift_end is not after shift_start,
                or any cumulative time value is negative.
        """
        if self.shift_end <= self.shift_start:
            raise ConfigurationError("Shift shift_end must be after shift_start.")
        if self.working_time_minutes < 0:
            raise ConfigurationError("working_time_minutes cannot be negative.")
        if self.rest_time_minutes < 0:
            raise ConfigurationError("rest_time_minutes cannot be negative.")