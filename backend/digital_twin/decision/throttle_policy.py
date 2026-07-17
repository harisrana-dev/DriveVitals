"""ThrottlePolicy: converts speed intent into a normalized throttle request.

Responsible only for `throttle_request`, in [0.0, 1.0]. When the target
speed is at or below the current speed, throttle is always 0.0 --
slowing down is BrakingPolicy's responsibility, not negative throttle.
"""

from __future__ import annotations

from digital_twin.decision.fatigue_model import FatigueResult
from digital_twin.decision.personalities import PersonalityProfile

#: Speed deficit, in km/h, that alone would saturate throttle to 1.0
#: for a driver with acceleration_bias == 1.0 and no fatigue.
_REFERENCE_SPEED_DEFICIT_KMH: float = 30.0


class ThrottlePolicy:
    """Converts a speed deficit into a normalized throttle request.

    Stateless: `compute_throttle` is a pure function of its arguments.
    """

    def compute_throttle(
        self,
        current_speed_kmh: float,
        target_speed_kmh: float,
        fatigue: FatigueResult,
        personality: PersonalityProfile,
    ) -> float:
        """Compute the throttle request needed to reach the target speed.

        Args:
            current_speed_kmh: The vehicle's current speed.
            target_speed_kmh: The speed selected by SpeedPolicy.
            fatigue: The driver's current fatigue evaluation; higher
                fatigue slows the driver's throttle response.
            personality: The driver's resolved personality parameters;
                `acceleration_bias` scales responsiveness, while
                `fuel_saving_factor` tempers it back down.

        Returns:
            Normalized throttle request in [0.0, 1.0]. Always 0.0 when
            `target_speed_kmh <= current_speed_kmh`.
        """
        speed_deficit = target_speed_kmh - current_speed_kmh
        if speed_deficit <= 0.0:
            return 0.0

        # A fuel-saving driver applies less throttle for the same
        # deficit; a fatigued driver reacts more sluggishly (lower
        # effective gain, not zero -- fatigue slows response, it does
        # not disable it).
        effective_gain = personality.acceleration_bias * (
            1.0 - 0.5 * personality.fuel_saving_factor
        )
        effective_gain /= fatigue.reaction_multiplier

        throttle = (speed_deficit / _REFERENCE_SPEED_DEFICIT_KMH) * effective_gain
        return min(1.0, max(0.0, throttle))