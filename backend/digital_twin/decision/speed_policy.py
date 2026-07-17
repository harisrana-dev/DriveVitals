"""SpeedPolicy: selects the driver's target speed for the current tick.

Responsible only for choosing `target_speed_kmh` -- never throttle,
braking, or any vehicle state. The configured speed limit is always
treated as a hard ceiling; every other input can only scale the target
speed downward (or, for personality speed_bias only, slightly upward,
but never past the limit).
"""

from __future__ import annotations

from digital_twin.common.enums import RoadCondition, WeatherCondition
from digital_twin.decision.decision_context import DecisionContext
from digital_twin.decision.fatigue_model import FatigueResult
from digital_twin.decision.personalities import PersonalityProfile
from digital_twin.entities.route import TrafficDensity

#: Multiplier applied per weather condition. 1.0 means no reduction.
_WEATHER_SPEED_FACTORS: dict[WeatherCondition, float] = {
    WeatherCondition.CLEAR: 1.00,
    WeatherCondition.RAIN: 0.85,
    WeatherCondition.FOG: 0.70,
    WeatherCondition.SNOW: 0.60,
    WeatherCondition.STORM: 0.55,
}

#: Multiplier applied per traffic density level.
_TRAFFIC_SPEED_FACTORS: dict[TrafficDensity, float] = {
    TrafficDensity.LOW: 1.00,
    TrafficDensity.MODERATE: 0.90,
    TrafficDensity.HIGH: 0.70,
    TrafficDensity.SEVERE: 0.45,
}

#: Multiplier applied per discrete road condition/event.
_ROAD_CONDITION_SPEED_FACTORS: dict[RoadCondition, float] = {
    RoadCondition.NORMAL: 1.00,
    RoadCondition.CONGESTED: 0.75,
    RoadCondition.CONSTRUCTION: 0.65,
    RoadCondition.ACCIDENT: 0.50,
    RoadCondition.CLOSED: 0.0,
}

#: Maximum fractional speed reduction fatigue alone can cause, before
#: the driver's personality risk_tolerance tempers it.
_MAX_FATIGUE_SPEED_REDUCTION: float = 0.35

#: Fractional speed reduction applied when carrying fragile cargo.
_FRAGILE_CARGO_SPEED_REDUCTION: float = 0.10

#: Fractional speed reduction applied when carrying hazardous cargo.
_HAZARDOUS_CARGO_SPEED_REDUCTION: float = 0.15


class SpeedPolicy:
    """Selects a target speed from conditions, fatigue, cargo, and personality.

    Stateless: `select_target_speed` is a pure function of its
    arguments.
    """

    def select_target_speed(
        self,
        context: DecisionContext,
        personality: PersonalityProfile,
        fatigue: FatigueResult,
    ) -> float:
        """Compute the target speed for the current tick.

        Args:
            context: Aggregated decision inputs for this tick.
            personality: The driver's resolved personality parameters.
            fatigue: The driver's current fatigue evaluation.

        Returns:
            Target speed, in km/h. Always in
            `[0.0, context.current_speed_limit_kmh]`.
        """
        speed_limit = context.current_speed_limit_kmh
        if speed_limit <= 0.0:
            return 0.0

        weather_factor = _WEATHER_SPEED_FACTORS.get(context.environment.weather, 1.0)
        traffic_factor = _TRAFFIC_SPEED_FACTORS.get(
            context.environment.traffic_density, 1.0
        )
        road_factor = _ROAD_CONDITION_SPEED_FACTORS.get(
            context.environment.road_condition, 1.0
        )

        # Fatigue reduces the target speed; a higher risk_tolerance
        # tempers (but never eliminates) that reduction.
        fatigue_reduction = (
            fatigue.fatigue_score
            * _MAX_FATIGUE_SPEED_REDUCTION
            * (1.0 - personality.risk_tolerance)
        )
        fatigue_factor = 1.0 - fatigue_reduction

        cargo_factor = 1.0
        if context.cargo is not None:
            if context.cargo.is_fragile:
                cargo_factor -= _FRAGILE_CARGO_SPEED_REDUCTION
            if context.cargo.is_hazardous:
                cargo_factor -= _HAZARDOUS_CARGO_SPEED_REDUCTION
        cargo_factor = max(0.0, cargo_factor)

        target_speed = (
            speed_limit
            * personality.speed_bias
            * weather_factor
            * traffic_factor
            * road_factor
            * fatigue_factor
            * cargo_factor
        )

        # The speed limit is always a hard ceiling, regardless of how
        # favorably speed_bias and the other factors combine.
        return min(speed_limit, max(0.0, target_speed))