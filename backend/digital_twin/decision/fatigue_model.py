"""FatigueModel: smooth, deterministic driver fatigue progression.

Fatigue is modeled as a continuous function of continuous driving
duration, accumulated shift duration, time-of-day (circadian effect),
and recovery from recent breaks -- rather than a lookup table of
discrete thresholds. Two boolean flags (`requires_break`,
`critical_fatigue`) are still threshold-based, since a downstream
consumer needs a clear yes/no signal; those thresholds are named
constants rather than values buried in conditionals.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from digital_twin.common.exceptions import ConfigurationError

# --- Time constants (hours/minutes to reach ~63% of maximum effect) -------

#: Time constant for fatigue accumulation from continuous driving.
_DRIVE_TIME_CONSTANT_HOURS: float = 6.0

#: Time constant for fatigue accumulation from total shift duration.
_SHIFT_TIME_CONSTANT_HOURS: float = 10.0

#: Time constant for fatigue recovery from a break.
_BREAK_TIME_CONSTANT_MINUTES: float = 25.0

# --- Circadian rhythm parameters -------------------------------------------

#: Maximum circadian fatigue contribution (fraction of total fatigue).
_CIRCADIAN_AMPLITUDE: float = 0.20

#: Hour of day (24h) at which circadian alertness is lowest.
_CIRCADIAN_TROUGH_HOUR: float = 4.0

# --- Component weights (sum to 1.0) ----------------------------------------

_DRIVE_WEIGHT: float = 0.5
_SHIFT_WEIGHT: float = 0.3
_CIRCADIAN_WEIGHT: float = 0.2

# --- Recovery and reaction scaling -----------------------------------------

#: Fraction of accumulated fatigue a full break can remove.
_RECOVERY_EFFECTIVENESS: float = 0.9

#: Maximum multiplier added to reaction time at full (1.0) fatigue.
_MAX_REACTION_SLOWDOWN: float = 1.5

# --- Flag thresholds --------------------------------------------------------

#: Fatigue score at or above which a break is recommended.
_REQUIRES_BREAK_THRESHOLD: float = 0.6

#: Fatigue score at or above which fatigue is considered critical/unsafe.
_CRITICAL_FATIGUE_THRESHOLD: float = 0.85


@dataclass(frozen=True)
class FatigueResult:
    """Output of a single FatigueModel evaluation.

    Attributes:
        fatigue_score: Overall fatigue, 0.0 (fully rested) to 1.0
            (maximally fatigued).
        alertness: Complement of fatigue_score (`1.0 - fatigue_score`),
            provided so consumers don't need to invert it themselves.
        reaction_multiplier: Multiplier to apply to baseline reaction
            time/response gain; 1.0 at zero fatigue, increasing smoothly
            toward `1.0 + _MAX_REACTION_SLOWDOWN` as fatigue approaches 1.0.
        requires_break: Whether fatigue has reached the level at which
            a break is recommended.
        critical_fatigue: Whether fatigue has reached a level considered
            unsafe to continue driving.
    """

    fatigue_score: float
    alertness: float
    reaction_multiplier: float
    requires_break: bool
    critical_fatigue: bool


class FatigueModel:
    """Computes driver fatigue as a smooth function of its inputs.

    Stateless: every call to `compute` is a pure function of its
    arguments. The model itself holds no per-driver mutable state --
    callers (the Decision Layer) are responsible for supplying each
    driver's current continuous driving/break/shift durations, which
    are owned and tracked by existing Sprint 1 managers/entities.
    """

    def compute(
        self,
        continuous_driving_hours: float,
        break_duration_minutes: float,
        shift_duration_hours: float,
        time_of_day_hour: float,
    ) -> FatigueResult:
        """Evaluate fatigue for a single point in simulated time.

        Args:
            continuous_driving_hours: Hours driven continuously since
                the last break.
            break_duration_minutes: Duration of the most recent break,
                in minutes (0.0 if no break has been taken).
            shift_duration_hours: Total elapsed duration of the current
                shift, in hours.
            time_of_day_hour: Current time of day, expressed as hours
                since midnight (0.0-24.0, fractional).

        Returns:
            A FatigueResult describing the driver's current fatigue
            state.

        Raises:
            ConfigurationError: If any duration argument is negative,
                or time_of_day_hour is outside [0.0, 24.0).
        """
        if continuous_driving_hours < 0:
            raise ConfigurationError("continuous_driving_hours cannot be negative.")
        if break_duration_minutes < 0:
            raise ConfigurationError("break_duration_minutes cannot be negative.")
        if shift_duration_hours < 0:
            raise ConfigurationError("shift_duration_hours cannot be negative.")
        if not (0.0 <= time_of_day_hour < 24.0):
            raise ConfigurationError("time_of_day_hour must be in [0.0, 24.0).")

        drive_fatigue = 1.0 - math.exp(
            -continuous_driving_hours / _DRIVE_TIME_CONSTANT_HOURS
        )
        shift_fatigue = 1.0 - math.exp(-shift_duration_hours / _SHIFT_TIME_CONSTANT_HOURS)

        # Smooth circadian curve: peaks at _CIRCADIAN_TROUGH_HOUR, troughs
        # 12 hours away, with no hard cutovers between "day" and "night".
        phase = 2.0 * math.pi * (time_of_day_hour - _CIRCADIAN_TROUGH_HOUR) / 24.0
        circadian_fatigue = _CIRCADIAN_AMPLITUDE * (1.0 + math.cos(phase)) / 2.0

        raw_fatigue = (
            _DRIVE_WEIGHT * drive_fatigue
            + _SHIFT_WEIGHT * shift_fatigue
            + _CIRCADIAN_WEIGHT * circadian_fatigue
        )

        recovery_factor = 1.0 - math.exp(
            -break_duration_minutes / _BREAK_TIME_CONSTANT_MINUTES
        )
        fatigue_score = raw_fatigue * (1.0 - recovery_factor * _RECOVERY_EFFECTIVENESS)
        fatigue_score = min(1.0, max(0.0, fatigue_score))

        alertness = 1.0 - fatigue_score
        reaction_multiplier = 1.0 + fatigue_score * _MAX_REACTION_SLOWDOWN

        return FatigueResult(
            fatigue_score=fatigue_score,
            alertness=alertness,
            reaction_multiplier=reaction_multiplier,
            requires_break=fatigue_score >= _REQUIRES_BREAK_THRESHOLD,
            critical_fatigue=fatigue_score >= _CRITICAL_FATIGUE_THRESHOLD,
        )