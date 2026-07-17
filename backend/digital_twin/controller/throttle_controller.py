"""ThrottleController: translates driver intent into a throttle command.

Responsible only for `throttle_percentage`. Never computes RPM,
acceleration, or fuel consumption -- it only decides how far down the
"virtual pedal" is pressed, smoothed so it never jumps instantly.
"""

from __future__ import annotations

from digital_twin.controller.controller_limits import (
    ControllerLimits,
    apply_dead_zone,
    clamp_throttle,
    rate_limit,
)
from digital_twin.decision.driver_intent import DriverIntent
from digital_twin.entities.vehicle import Vehicle, VehicleSpecification


class ThrottleController:
    """Computes a smoothed, clamped throttle command from driver intent.

    Stateless: `compute_throttle` is a pure function of its arguments.
    The caller supplies `previous_throttle` (typically the previous
    tick's `VehicleActuation.throttle_percentage`) so this class holds
    no state of its own.
    """

    def compute_throttle(
        self,
        intent: DriverIntent,
        vehicle: Vehicle,
        specification: VehicleSpecification,
        previous_throttle: float,
        limits: ControllerLimits,
    ) -> float:
        """Compute this tick's throttle command.

        Args:
            intent: The driver's intent for this tick. `throttle_request`
                is the primary input; a positive `brake_request` or
                `request_emergency_stop` always forces throttle to 0.0,
                since a real ECU never applies throttle and brake at
                once.
            vehicle: The vehicle this command is being computed for.
                Reserved for future per-vehicle throttle-response
                tuning (e.g. reading `vehicle.state` for load-based
                response); unused by the current linear model.
            specification: The vehicle's static specification. Reserved
                for future fuel-type/transmission-specific throttle
                mapping (e.g. electric vs. diesel throttle response
                curves); unused by the current linear model.
            previous_throttle: The throttle percentage commanded on the
                previous tick, used to rate-limit this tick's command.
            limits: Active ControllerLimits.

        Returns:
            Normalized throttle command in `[0.0, limits.max_throttle]`.
            Always 0.0 when braking or an emergency stop is requested.
        """
        del vehicle, specification  # Reserved extension points; unused today.

        if intent.request_emergency_stop or intent.brake_request > 0.0:
            target_throttle = 0.0
        else:
            target_throttle = apply_dead_zone(
                intent.throttle_request, limits.throttle_dead_zone
            )
            target_throttle = clamp_throttle(target_throttle, limits)

        smoothed_throttle = rate_limit(
            previous_value=previous_throttle,
            target_value=target_throttle,
            max_delta=limits.throttle_max_delta_per_tick,
        )
        return clamp_throttle(smoothed_throttle, limits)