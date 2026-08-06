"""
Canonical driver safety score.

Single owner of trip- and driver-level safety scoring. The score is
normalised by distance so that the same number of events hurts far more
on a short trip than on a long one (5 harsh brakes over 10 km is worse
than 5 harsh brakes over 500 km), and a driver's score recovers with
clean driving instead of being permanently pinned to zero by an early
bad trip.
"""

from backend.analytics.behaviour.aggregation.summary import (
    DriverBehaviourSummary,
)
from backend.analytics.driver_statistics.config import (
    SAFETY_DENSITY_SENSITIVITY,
    SAFETY_START,
    SAFETY_WEIGHT_HARD_ACCELERATION,
    SAFETY_WEIGHT_HARD_BRAKE,
    SAFETY_WEIGHT_HIGH_RPM,
    SAFETY_WEIGHT_OVERSPEED,
    clamp_score,
    events_per_km,
)


def compute_safety_score(
    *,
    harsh_braking_count: int,
    harsh_acceleration_count: int,
    overspeed_count: int,
    high_rpm_count: int = 0,
    distance_km: float,
) -> float:
    """
    Compute a safety score in [0, 100] from behaviour counts and the
    distance over which they occurred.

    The score starts at SAFETY_START and decays toward zero as the
    density of weighted misbehaviour grows. Because the deduction is
    density-based rather than count-based, the score is never a
    permanent penalty accumulator: clean driving lowers the density and
    the score recovers.
    """
    weighted_density = events_per_km(
        (
            harsh_braking_count * SAFETY_WEIGHT_HARD_BRAKE
            + harsh_acceleration_count * SAFETY_WEIGHT_HARD_ACCELERATION
            + overspeed_count * SAFETY_WEIGHT_OVERSPEED
            + high_rpm_count * SAFETY_WEIGHT_HIGH_RPM
        ),
        distance_km,
    )

    if weighted_density == float("inf"):
        return 0.0

    score = SAFETY_START / (
        1.0 + weighted_density * SAFETY_DENSITY_SENSITIVITY
    )

    return clamp_score(round(score, 2))


def compute_safety_score_for_summary(
    summary: DriverBehaviourSummary,
    *,
    distance_km: float,
) -> float:
    """
    Compute a safety score from a completed-trip behaviour summary.

    ``distance_km`` must be the distance covered during the trip, not a
    vehicle's lifetime odometer, otherwise the density normalisation is
    meaningless.
    """
    return compute_safety_score(
        harsh_braking_count=summary.harsh_braking_count,
        harsh_acceleration_count=summary.aggressive_throttle_event_count,
        overspeed_count=summary.speeding_event_count,
        high_rpm_count=summary.high_rpm_event_count,
        distance_km=distance_km,
    )
