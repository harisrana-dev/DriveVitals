"""BrakingPolicy: converts deceleration need and hazards into a brake request.

Responsible only for `brake_request`, in [0.0, 1.0]. Emergency braking
is an explicit override to 1.0; otherwise braking is driven by how
much the vehicle needs to slow down to reach the target speed, scaled
by traffic/road hazard severity and the driver's personality.
"""

from __future__ import annotations

from digital_twin.common.enums import RoadCondition
from digital_twin.decision.personalities import PersonalityProfile
from digital_twin.entities.environment import EnvironmentSnapshot
from digital_twin.entities.route import TrafficDensity

#: Speed excess, in km/h, that alone would saturate braking to 1.0 for
#: a driver with braking_aggressiveness == 1.0 and no hazard scaling.
_REFERENCE_SPEED_EXCESS_KMH: float = 30.0

#: Additional brake-request scaling for hazardous road conditions.
_ROAD_HAZARD_BRAKE_FACTORS: dict[RoadCondition, float] = {
    RoadCondition.NORMAL: 1.00,
    RoadCondition.CONGESTED: 1.10,
    RoadCondition.CONSTRUCTION: 1.15,
    RoadCondition.ACCIDENT: 1.30,
    RoadCondition.CLOSED: 1.30,
}

#: Additional brake-request scaling for heavy traffic (closer following
#: vehicles require more responsive, slightly stronger braking).
_TRAFFIC_BRAKE_FACTORS: dict[TrafficDensity, float] = {
    TrafficDensity.LOW: 1.00,
    TrafficDensity.MODERATE: 1.05,
    TrafficDensity.HIGH: 1.15,
    TrafficDensity.SEVERE: 1.25,
}


class BrakingPolicy:
    """Converts deceleration need and hazards into a normalized brake request.

    Stateless: `compute_brake` is a pure function of its arguments.
    """

    def compute_brake(
        self,
        current_speed_kmh: float,
        target_speed_kmh: float,
        environment: EnvironmentSnapshot,
        personality: PersonalityProfile,
        emergency: bool = False,
    ) -> float:
        """Compute the brake request needed to reach the target speed.

        Args:
            current_speed_kmh: The vehicle's current speed.
            target_speed_kmh: The speed selected by SpeedPolicy.
            environment: Current environmental conditions, used to
                scale braking for hazardous road/traffic conditions.
            personality: The driver's resolved personality parameters;
                `braking_aggressiveness` scales how hard the driver
                brakes for a given deceleration need.
            emergency: If True, overrides all other inputs and returns
                a full emergency brake request.

        Returns:
            Normalized brake request in [0.0, 1.0]. Always 0.0 when
            `target_speed_kmh >= current_speed_kmh` and not emergency.
        """
        if emergency:
            return 1.0

        speed_excess = current_speed_kmh - target_speed_kmh
        if speed_excess <= 0.0:
            return 0.0

        road_factor = _ROAD_HAZARD_BRAKE_FACTORS.get(environment.road_condition, 1.0)
        traffic_factor = _TRAFFIC_BRAKE_FACTORS.get(environment.traffic_density, 1.0)

        brake = (
            (speed_excess / _REFERENCE_SPEED_EXCESS_KMH)
            * personality.braking_aggressiveness
            * road_factor
            * traffic_factor
        )
        return min(1.0, max(0.0, brake))