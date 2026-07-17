"""BrakeController: translates driver intent into a brake command.

Responsible only for `brake_percentage`. Emergency stop requests always
dominate: they bypass smoothing entirely and always win over throttle,
matching how a real ECU treats an emergency brake signal.
"""

from __future__ import annotations

from digital_twin.controller.controller_limits import (
    ControllerLimits,
    apply_dead_zone,
    clamp_brake,
    rate_limit,
)
from digital_twin.decision.driver_intent import DriverIntent


class BrakeController:
    """Computes a smoothed, clamped brake command from driver intent.

    Stateless: `compute_brake` is a pure function of its arguments. The
    caller supplies `previous_brake` (typically the previous tick's
    `VehicleActuation.brake_percentage`) so this class holds no state
    of its own.
    """

    def compute_brake(
        self,
        intent: DriverIntent,
        previous_brake: float,
        limits: ControllerLimits,
    ) -> float:
        """Compute this tick's brake command.

        Args:
            intent: The driver's intent for this tick.
                `request_emergency_stop` immediately commands full
                braking, unsmoothed. Otherwise `brake_request` is
                clamped, dead-zoned, and rate-limited.
            previous_brake: The brake percentage commanded on the
                previous tick, used to rate-limit non-emergency
                braking so it doesn't oscillate.
            limits: Active ControllerLimits.

        Returns:
            Normalized brake command in `[0.0, limits.max_brake]`.
            Equal to `limits.max_brake` immediately whenever
            `intent.request_emergency_stop` is True -- emergency
            braking is never smoothed and always dominates throttle.
        """
        if intent.request_emergency_stop:
            return limits.max_brake

        target_brake = apply_dead_zone(intent.brake_request, limits.brake_dead_zone)
        target_brake = clamp_brake(target_brake, limits)

        smoothed_brake = rate_limit(
            previous_value=previous_brake,
            target_value=target_brake,
            max_delta=limits.brake_max_delta_per_tick,
        )
        return clamp_brake(smoothed_brake, limits)