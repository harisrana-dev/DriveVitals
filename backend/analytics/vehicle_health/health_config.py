"""
Vehicle health configuration.

Central home for every constant used by the Vehicle Health subsystem:

    * health score -> status thresholds
    * subsystem weighting for the overall score
    * per-subsystem analyzer thresholds
    * shared scoring helpers

Constants must never be scattered across analyzer modules. New knobs
are introduced here first and consumed through HealthConfig.
"""

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from math import sqrt

from backend.analytics.vehicle_health.models.subsystem_health import (
    HealthStatus,
    Subsystem,
)
from backend.telemetry.models.telemetry_sample import TelemetrySample


@dataclass(frozen=True, slots=True)
class StatusThresholds:
    """Thresholds mapping a health score to a HealthStatus."""

    healthy_min: float = 90.0
    warning_min: float = 70.0


@dataclass(frozen=True, slots=True)
class EngineThresholds:
    """Engine analyzer thresholds."""

    redline_rpm: float = 6200.0
    redline_deduction: float = 30.0

    sustained_rpm: float = 4500.0
    sustained_rpm_fraction: float = 0.30
    sustained_rpm_deduction: float = 25.0

    overheat_temp_c: float = 105.0
    overheat_span_c: float = 15.0
    overheat_deduction: float = 25.0

    max_load_percent: float = 85.0
    max_load_fraction: float = 0.40
    max_load_deduction: float = 25.0

    throttle_abuse_percent: float = 90.0
    throttle_abuse_fraction: float = 0.30
    throttle_abuse_deduction: float = 20.0

    aggressive_throttle_event_deduction: float = 4.0
    aggressive_throttle_event_cap: int = 4


@dataclass(frozen=True, slots=True)
class BrakeThresholds:
    """Brake analyzer thresholds."""

    harsh_brake_pressure: float = 0.80
    harsh_pressure_deduction: float = 10.0

    hard_brake_pressure: float = 0.60
    hard_brake_fraction: float = 0.25
    hard_brake_deduction: float = 15.0

    harsh_brake_event_deduction: float = 8.0
    harsh_brake_event_cap: int = 5


@dataclass(frozen=True, slots=True)
class CoolingThresholds:
    """Cooling analyzer thresholds."""

    overheat_temp_c: float = 100.0
    overheat_span_c: float = 15.0
    overheat_deduction: float = 40.0

    elevated_temp_c: float = 90.0
    elevated_span_c: float = 10.0
    elevated_deduction: float = 10.0

    stability_stddev_c: float = 3.0
    stability_span_c: float = 10.0
    stability_deduction: float = 15.0

    max_load_percent: float = 85.0
    max_load_deduction: float = 10.0


@dataclass(frozen=True, slots=True)
class TransmissionThresholds:
    """Transmission analyzer thresholds."""

    low_speed_kmh: float = 30.0
    stress_rpm: float = 4500.0
    stress_throttle_percent: float = 70.0
    stress_deduction: float = 20.0

    stress_fraction: float = 0.20
    stress_fraction_deduction: float = 25.0


@dataclass(frozen=True, slots=True)
class FuelSystemThresholds:
    """Fuel system analyzer thresholds."""

    min_speed_kmh: float = 25.0
    normal_load_min_percent: float = 20.0
    normal_load_max_percent: float = 70.0
    min_efficiency_km_per_l: float = 6.0
    efficiency_deduction: float = 30.0

    high_fuel_rate_lph: float = 25.0
    high_consumption_fraction: float = 0.15
    high_consumption_deduction: float = 15.0

    abuse_throttle_percent: float = 85.0
    abuse_deduction: float = 5.0


_SUBSYSTEM_WEIGHTS: dict[Subsystem, float] = {
    Subsystem.ENGINE: 0.30,
    Subsystem.COOLING: 0.20,
    Subsystem.BRAKES: 0.20,
    Subsystem.TRANSMISSION: 0.15,
    Subsystem.FUEL_SYSTEM: 0.15,
}


@dataclass(frozen=True, slots=True)
class HealthConfig:
    """
    Aggregate configuration for the Vehicle Health subsystem.

    All constants referenced by the engine and the analyzers live here.
    """

    weights: Mapping[Subsystem, float] = field(
        default_factory=lambda: dict(_SUBSYSTEM_WEIGHTS)
    )
    status: StatusThresholds = StatusThresholds()
    window_size: int = 20
    engine: EngineThresholds = EngineThresholds()
    brake: BrakeThresholds = BrakeThresholds()
    cooling: CoolingThresholds = CoolingThresholds()
    transmission: TransmissionThresholds = TransmissionThresholds()
    fuel_system: FuelSystemThresholds = FuelSystemThresholds()


DEFAULT_HEALTH_CONFIG = HealthConfig()


def clamp_score(score: float) -> float:
    """Clamp a health score into the valid [0, 100] range."""
    return min(100.0, max(0.0, score))


def status_for_score(score: float, thresholds: StatusThresholds) -> HealthStatus:
    """Map a health score to a HealthStatus using centralized thresholds."""
    if score >= thresholds.healthy_min:
        return HealthStatus.HEALTHY
    if score >= thresholds.warning_min:
        return HealthStatus.WARNING
    return HealthStatus.CRITICAL


def excess_penalty(value: float, threshold: float, span: float, amount: float) -> float:
    """
    Continuous penalty proportional to how far `value` exceeds `threshold`.

    Returns 0 when value <= threshold and at most `amount` when value
    reaches threshold + span.
    """
    if span <= 0.0:
        raise ValueError("span must be positive")
    if amount <= 0.0:
        return 0.0
    excess = max(0.0, value - threshold)
    return min(amount, amount * excess / span)


def fraction_penalty(fraction: float, floor: float, amount: float) -> float:
    """
    Continuous penalty for a window fraction above a floor.

    Returns 0 when fraction <= floor and at most `amount` when fraction
    reaches 1.0.
    """
    if not 0.0 <= floor < 1.0:
        raise ValueError("floor must be in [0, 1)")
    if amount <= 0.0:
        return 0.0
    if fraction <= floor:
        return 0.0
    progress = (fraction - floor) / (1.0 - floor)
    return min(amount, progress * amount)


def window_fraction(
    samples: Sequence[TelemetrySample],
    predicate: Callable[[TelemetrySample], bool],
) -> float:
    """Fraction of samples in the window for which `predicate` is true."""
    if not samples:
        return 0.0
    return sum(predicate(sample) for sample in samples) / len(samples)


def mean(values: Sequence[float]) -> float:
    """Arithmetic mean of the values; 0.0 for an empty sequence."""
    if not values:
        return 0.0
    return sum(values) / len(values)


def standard_deviation(values: Sequence[float]) -> float:
    """Population standard deviation; 0.0 when fewer than two values."""
    if len(values) < 2:
        return 0.0
    average = mean(values)
    variance = sum((value - average) ** 2 for value in values) / len(values)
    return sqrt(variance)


__all__ = [
    "StatusThresholds",
    "EngineThresholds",
    "BrakeThresholds",
    "CoolingThresholds",
    "TransmissionThresholds",
    "FuelSystemThresholds",
    "HealthConfig",
    "DEFAULT_HEALTH_CONFIG",
    "clamp_score",
    "status_for_score",
    "excess_penalty",
    "fraction_penalty",
    "window_fraction",
    "mean",
    "standard_deviation",
]
