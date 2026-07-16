"""Driver entity: domain data describing a single fleet driver.

Pure data model -- no fatigue calculation, no scheduling logic, no
mutation of Vehicle state. Those belong to future sprints (Decision
Engine updates Driver intent; Physics updates Vehicle state; this
entity only stores what the current values are).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from digital_twin.common.enums import DriverStatus
from digital_twin.common.exceptions import ConfigurationError


class ExperienceLevel(str, Enum):
    """Driver experience tier."""

    TRAINEE = "TRAINEE"
    JUNIOR = "JUNIOR"
    EXPERIENCED = "EXPERIENCED"
    SENIOR = "SENIOR"
    VETERAN = "VETERAN"


class BehaviourProfile(str, Enum):
    """Driving style/behaviour archetype.

    Mirrors the archetypes referenced by DriveVitals' earlier
    simulator work (city, aggressive, highway, delivery-van driver
    styles); stored here as data only -- how a profile actually
    influences driving is a future Decision Engine concern.
    """

    CAUTIOUS = "CAUTIOUS"
    STANDARD = "STANDARD"
    AGGRESSIVE = "AGGRESSIVE"
    ECO_FOCUSED = "ECO_FOCUSED"


@dataclass
class Driver:
    """A single fleet driver and their persistent domain state.

    Attributes:
        driver_id: Unique identifier for the driver.
        name: Driver's display name.
        license_number: Driver's license number.
        experience_level: Driver's experience tier.
        behaviour_profile: Driver's driving style archetype.
        fatigue_level: Current fatigue level, on a 0.0 (fully rested)
            to 1.0 (fully fatigued) scale.
        performance_score: Overall performance score, 0.0 to 100.0.
        current_shift_id: Id of the shift currently assigned, if any.
        current_vehicle_id: Id of the vehicle currently assigned, if any.
        current_trip_id: Id of the trip currently assigned, if any.
        working_hours: Cumulative working hours across all shifts.
        break_time_minutes: Cumulative break time, in minutes, across
            all shifts.
        completed_trip_ids: Ids of trips this driver has completed.
        violation_count: Count of recorded safety/compliance violations.
        fuel_efficiency_score: Fuel efficiency score, 0.0 to 100.0.
        safety_score: Safety score, 0.0 to 100.0.
        status: Current availability status.
    """

    driver_id: str
    name: str
    license_number: str
    experience_level: ExperienceLevel = ExperienceLevel.JUNIOR
    behaviour_profile: BehaviourProfile = BehaviourProfile.STANDARD
    fatigue_level: float = 0.0
    performance_score: float = 100.0
    current_shift_id: str | None = None
    current_vehicle_id: str | None = None
    current_trip_id: str | None = None
    working_hours: float = 0.0
    break_time_minutes: float = 0.0
    completed_trip_ids: list[str] = field(default_factory=list)
    violation_count: int = 0
    fuel_efficiency_score: float = 100.0
    safety_score: float = 100.0
    status: DriverStatus = DriverStatus.OFF_DUTY

    def __post_init__(self) -> None:
        """Validate invariants on constructed values.

        Raises:
            ConfigurationError: If any score/level/count is outside its
                valid range, or any cumulative value is negative.
        """
        if not (0.0 <= self.fatigue_level <= 1.0):
            raise ConfigurationError("fatigue_level must be between 0.0 and 1.0.")
        for score_name in ("performance_score", "fuel_efficiency_score", "safety_score"):
            value = getattr(self, score_name)
            if not (0.0 <= value <= 100.0):
                raise ConfigurationError(f"{score_name} must be between 0.0 and 100.0.")
        if self.working_hours < 0:
            raise ConfigurationError("working_hours cannot be negative.")
        if self.break_time_minutes < 0:
            raise ConfigurationError("break_time_minutes cannot be negative.")
        if self.violation_count < 0:
            raise ConfigurationError("violation_count cannot be negative.")