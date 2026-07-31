"""
DriverStatistics model.

Immutable aggregate of a driver's behaviour and trip history. Produced
by the DriverStatisticsEngine. Contains no scoring logic.
"""

from dataclasses import dataclass


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
    total_distance: float
    total_trips: int
