"""DriverBehaviourEngine: orchestrator for the Decision Layer.

Reads a `DecisionContext`, computes fatigue, resolves the driver's
personality, delegates to `SpeedPolicy`, `ThrottlePolicy`, and
`BrakingPolicy`, and returns a single `DriverIntent`. This is the only
entry point the execution pipeline (positioned after DispatchManager,
before the Vehicle Controller) is expected to call.

The engine never mutates `Vehicle`, `Driver`, or any other entity, and
never generates telemetry or performs physics -- it only decides what
the driver wants.
"""

from __future__ import annotations

from digital_twin.common.enums import RoadCondition, TripStatus
from digital_twin.decision.braking_policy import BrakingPolicy
from digital_twin.decision.decision_context import DecisionContext
from digital_twin.decision.driver_intent import DriverIntent
from digital_twin.decision.fatigue_model import FatigueModel, FatigueResult
from digital_twin.decision.personalities import (
    PersonalityProfile,
    get_personality_profile,
    resolve_personality_type,
)
from digital_twin.decision.speed_policy import SpeedPolicy
from digital_twin.decision.throttle_policy import ThrottlePolicy
from digital_twin.entities.route import TrafficDensity

#: Reference peak acceleration used to convert a normalized throttle
#: request into a desired longitudinal acceleration, in m/s^2. This is
#: an intent-space reference only -- it does not model any specific
#: vehicle's real performance, which is the Physics Engine's concern.
_REFERENCE_MAX_ACCELERATION_MPS2: float = 2.5

#: Reference peak deceleration used to convert a normalized brake
#: request into a desired longitudinal deceleration, in m/s^2.
_REFERENCE_MAX_DECELERATION_MPS2: float = 6.0

#: Road conditions considered severe enough, combined with severe
#: traffic, to justify an emergency stop request.
_EMERGENCY_ROAD_CONDITIONS: frozenset[RoadCondition] = frozenset(
    {RoadCondition.ACCIDENT}
)


class DriverBehaviourEngine:
    """Computes a driver's intent for the current tick from a DecisionContext.

    Depends only on the four Decision Layer building blocks
    (`FatigueModel`, `SpeedPolicy`, `ThrottlePolicy`, `BrakingPolicy`),
    each injected so the engine is independently testable with fakes or
    alternative policy implementations.
    """

    def __init__(
        self,
        fatigue_model: FatigueModel | None = None,
        speed_policy: SpeedPolicy | None = None,
        throttle_policy: ThrottlePolicy | None = None,
        braking_policy: BrakingPolicy | None = None,
    ) -> None:
        """Initialize the engine, defaulting to the standard policy set.

        Args:
            fatigue_model: Fatigue evaluator. Defaults to a new
                `FatigueModel`.
            speed_policy: Target speed selector. Defaults to a new
                `SpeedPolicy`.
            throttle_policy: Throttle request calculator. Defaults to a
                new `ThrottlePolicy`.
            braking_policy: Brake request calculator. Defaults to a new
                `BrakingPolicy`.
        """
        self._fatigue_model = fatigue_model or FatigueModel()
        self._speed_policy = speed_policy or SpeedPolicy()
        self._throttle_policy = throttle_policy or ThrottlePolicy()
        self._braking_policy = braking_policy or BrakingPolicy()

    def decide(self, context: DecisionContext) -> DriverIntent:
        """Compute this tick's DriverIntent from the given context.

        Args:
            context: Aggregated inputs for this decision.

        Returns:
            The resulting DriverIntent. Never mutates `context` or any
            entity it references.
        """
        personality_type = resolve_personality_type(context.driver)
        personality = get_personality_profile(personality_type)

        fatigue = self._fatigue_model.compute(
            continuous_driving_hours=context.continuous_driving_hours,
            break_duration_minutes=context.break_duration_minutes,
            shift_duration_hours=context.shift_duration_hours,
            time_of_day_hour=context.time_of_day_hour,
        )

        emergency = self._requires_emergency_stop(context, fatigue)
        trip_ending = self._trip_is_ending(context)

        target_speed_kmh = 0.0 if (emergency or trip_ending) else (
            self._speed_policy.select_target_speed(context, personality, fatigue)
        )

        throttle_request = 0.0
        brake_request = self._braking_policy.compute_brake(
            current_speed_kmh=context.current_speed_kmh,
            target_speed_kmh=target_speed_kmh,
            environment=context.environment,
            personality=personality,
            emergency=emergency,
        )
        if brake_request == 0.0:
            throttle_request = self._throttle_policy.compute_throttle(
                current_speed_kmh=context.current_speed_kmh,
                target_speed_kmh=target_speed_kmh,
                fatigue=fatigue,
                personality=personality,
            )

        desired_acceleration_mps2 = (
            throttle_request * _REFERENCE_MAX_ACCELERATION_MPS2
            - brake_request * _REFERENCE_MAX_DECELERATION_MPS2
        )

        overtake_requested = self._should_overtake(context, personality, target_speed_kmh)

        reason = self._explain(
            emergency=emergency,
            trip_ending=trip_ending,
            fatigue=fatigue,
            context=context,
            overtake_requested=overtake_requested,
        )

        return DriverIntent(
            target_speed_kmh=target_speed_kmh,
            desired_acceleration_mps2=desired_acceleration_mps2,
            throttle_request=throttle_request,
            brake_request=brake_request,
            steering_request=0.0,
            request_stop=trip_ending and not emergency,
            request_emergency_stop=emergency,
            request_lane_change=overtake_requested,
            overtake_requested=overtake_requested,
            reason=reason,
            decision_timestamp=context.tick_context.simulation_time,
        )

    def _requires_emergency_stop(
        self, context: DecisionContext, fatigue: FatigueResult
    ) -> bool:
        """Determine whether conditions warrant an emergency stop.

        Args:
            context: Aggregated decision inputs.
            fatigue: The driver's current fatigue evaluation.

        Returns:
            True if the road condition is severe under heavy traffic,
            or the driver's fatigue has reached the critical level.
        """
        hazardous_road = context.environment.road_condition in _EMERGENCY_ROAD_CONDITIONS
        heavy_traffic = context.environment.traffic_density in (
            TrafficDensity.HIGH,
            TrafficDensity.SEVERE,
        )
        return (hazardous_road and heavy_traffic) or fatigue.critical_fatigue

    def _trip_is_ending(self, context: DecisionContext) -> bool:
        """Determine whether the driver should be bringing the vehicle to a stop.

        Args:
            context: Aggregated decision inputs.

        Returns:
            True if there is no active trip, or the trip/road state
            indicates the vehicle should stop (e.g. the road ahead is
            closed).
        """
        if context.trip is None or context.trip.status in (
            TripStatus.COMPLETED,
            TripStatus.CANCELLED,
        ):
            return True
        return context.environment.road_condition == RoadCondition.CLOSED

    def _should_overtake(
        self,
        context: DecisionContext,
        personality: PersonalityProfile,
        target_speed_kmh: float,
    ) -> bool:
        """Determine whether the driver wants to overtake.

        A conservative, deterministic heuristic: only risk-tolerant
        personalities consider overtaking, and only when traffic is
        heavy enough that the current lane is likely moving below the
        driver's own target speed.

        Args:
            context: Aggregated decision inputs.
            personality: The driver's resolved personality parameters.
            target_speed_kmh: The speed selected by SpeedPolicy.

        Returns:
            True if the driver intends to overtake.
        """
        if target_speed_kmh <= 0.0:
            return False
        heavy_traffic = context.environment.traffic_density in (
            TrafficDensity.HIGH,
            TrafficDensity.SEVERE,
        )
        return heavy_traffic and personality.risk_tolerance >= 0.6

    def _explain(
        self,
        emergency: bool,
        trip_ending: bool,
        fatigue: FatigueResult,
        context: DecisionContext,
        overtake_requested: bool,
    ) -> str:
        """Build a concise, human-readable explanation for this intent.

        Args:
            emergency: Whether an emergency stop was requested.
            trip_ending: Whether the driver is bringing the trip to a
                stop.
            fatigue: The driver's current fatigue evaluation.
            context: Aggregated decision inputs.
            overtake_requested: Whether an overtake was requested.

        Returns:
            A short string naming the dominant factor(s) behind the
            computed intent.
        """
        if emergency:
            return (
                f"Emergency stop: road_condition="
                f"{context.environment.road_condition.value}, "
                f"traffic={context.environment.traffic_density.value}, "
                f"critical_fatigue={fatigue.critical_fatigue}"
            )
        if trip_ending:
            return "Bringing vehicle to a stop: trip ending or road closed."
        if fatigue.requires_break:
            return f"Reduced target speed due to fatigue (score={fatigue.fatigue_score:.2f})."
        if overtake_requested:
            return "Overtaking due to heavy traffic and driver risk tolerance."
        return (
            f"Cruising toward target speed under weather="
            f"{context.environment.weather.value}, "
            f"traffic={context.environment.traffic_density.value}."
        )