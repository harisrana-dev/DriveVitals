"""
DriverStatistics model.

Immutable aggregate of a driver's behaviour and trip history. Produced
by the DriverStatisticsEngine. Contains no scoring logic.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True, slots=True)
class DriverStatistics:
    """
    Purpose:
        Summarise one driver's aggregated behaviour and trip history.
    Inputs:
        Produced by the DriverStatisticsEngine.
    Outputs:
        Consumed by persistence and, in the future, by dashboard APIs.
    TODO:
        Decide whether efficiency_score should also include fuel-related
        telemetry beyond behaviour events and trips.
    """

    driver_id: str
    safety_score: float
    aggression_score: float
    efficiency_score: float
    total_events: int
    harsh_braking_count: int
    overspeed_count: int
    harsh_acceleration_count: int
    high_rpm_count: int = 0
    total_distance: float = 0.0
    total_trips: int = 0
    total_driving_time_seconds: int = 0
    total_fuel_used_liters: float = 0.0
    average_trip_score: Optional[float] = None
    fuel_efficiency: Optional[float] = None
