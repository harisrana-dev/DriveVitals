"""Configuration loader — bridges persisted Settings to the analytics runtime.

Reads from the ``system_settings`` table and constructs typed configuration
objects that the analytics engines consume.  Falls back to application
defaults when no persisted configuration exists.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.analytics.driver_statistics.config import (
    AGGRESSION_MAX_DENSITY,
    AGGRESSION_WEIGHT_HARD_ACCELERATION,
    AGGRESSION_WEIGHT_HARD_BRAKE,
    AGGRESSION_WEIGHT_OVERSPEED,
    EFFICIENCY_MAX_EVENTS_PER_KM,
    SAFETY_DENSITY_SENSITIVITY,
    SAFETY_WEIGHT_HARD_ACCELERATION,
    SAFETY_WEIGHT_HARD_BRAKE,
    SAFETY_WEIGHT_HIGH_RPM,
    SAFETY_WEIGHT_OVERSPEED,
)
from backend.analytics.vehicle_health.health_config import (
    BrakeThresholds,
    CoolingThresholds,
    DEFAULT_HEALTH_CONFIG,
    EngineThresholds,
    FuelSystemThresholds,
    HealthConfig,
    StatusThresholds,
    TransmissionThresholds,
)
from backend.analytics.vehicle_health.models.subsystem_health import Subsystem
from backend.db.models.system_settings import SystemSettings


async def load_health_config(session: AsyncSession) -> HealthConfig:
    """Load vehicle health configuration from the database.

    If no persisted row exists, returns ``DEFAULT_HEALTH_CONFIG``.
    If a persisted row exists but fails to parse, falls back to defaults.
    """
    result = await session.execute(
        select(SystemSettings).where(
            SystemSettings.category == "analytics"
        )
    )
    row = result.scalar_one_or_none()

    if row is None:
        return DEFAULT_HEALTH_CONFIG

    data = row.settings_data
    vh_data = data.get("vehicle_health")
    if vh_data is None:
        return DEFAULT_HEALTH_CONFIG

    try:
        status_data = vh_data.get("status", {})
        weights_data = vh_data.get("weights", {})

        weights = {}
        for sub in Subsystem:
            weights[sub] = weights_data.get(sub.value, 0.0)

        return HealthConfig(
            status=StatusThresholds(
                healthy_min=status_data.get("healthy_min", 90.0),
                warning_min=status_data.get("warning_min", 70.0),
            ),
            window_size=vh_data.get("window_size", 20),
            weights=weights,
            engine=EngineThresholds(**vh_data.get("engine", {})),
            brake=BrakeThresholds(**vh_data.get("brake", {})),
            cooling=CoolingThresholds(**vh_data.get("cooling", {})),
            transmission=TransmissionThresholds(
                **vh_data.get("transmission", {})
            ),
            fuel_system=FuelSystemThresholds(
                **vh_data.get("fuel_system", {})
            ),
        )
    except Exception:
        # Fall back to defaults on any parsing error
        return DEFAULT_HEALTH_CONFIG


def get_driver_statistics_config_from_data(
    data: dict | None,
) -> dict:
    """Extract driver statistics configuration from persisted settings data.

    Returns a dict with the configuration values that can be used by the
    score calculator.  Falls back to application defaults when data is None
    or incomplete.
    """
    if data is None:
        return _default_driver_stats_config()

    ds_data = data.get("driver_statistics")
    if ds_data is None:
        return _default_driver_stats_config()

    safety = ds_data.get("safety", {})
    aggression = ds_data.get("aggression", {})
    efficiency = ds_data.get("efficiency", {})

    return {
        "safety": {
            "weight_hard_brake": safety.get(
                "weight_hard_brake", SAFETY_WEIGHT_HARD_BRAKE
            ),
            "weight_hard_acceleration": safety.get(
                "weight_hard_acceleration", SAFETY_WEIGHT_HARD_ACCELERATION
            ),
            "weight_overspeed": safety.get(
                "weight_overspeed", SAFETY_WEIGHT_OVERSPEED
            ),
            "weight_high_rpm": safety.get(
                "weight_high_rpm", SAFETY_WEIGHT_HIGH_RPM
            ),
            "density_sensitivity": safety.get(
                "density_sensitivity", SAFETY_DENSITY_SENSITIVITY
            ),
        },
        "aggression": {
            "weight_hard_brake": aggression.get(
                "weight_hard_brake", AGGRESSION_WEIGHT_HARD_BRAKE
            ),
            "weight_hard_acceleration": aggression.get(
                "weight_hard_acceleration",
                AGGRESSION_WEIGHT_HARD_ACCELERATION,
            ),
            "weight_overspeed": aggression.get(
                "weight_overspeed", AGGRESSION_WEIGHT_OVERSPEED
            ),
            "max_density": aggression.get(
                "max_density", AGGRESSION_MAX_DENSITY
            ),
        },
        "efficiency": {
            "max_events_per_km": efficiency.get(
                "max_events_per_km", EFFICIENCY_MAX_EVENTS_PER_KM
            ),
        },
    }


def _default_driver_stats_config() -> dict:
    """Return the default driver statistics configuration."""
    return {
        "safety": {
            "weight_hard_brake": SAFETY_WEIGHT_HARD_BRAKE,
            "weight_hard_acceleration": SAFETY_WEIGHT_HARD_ACCELERATION,
            "weight_overspeed": SAFETY_WEIGHT_OVERSPEED,
            "weight_high_rpm": SAFETY_WEIGHT_HIGH_RPM,
            "density_sensitivity": SAFETY_DENSITY_SENSITIVITY,
        },
        "aggression": {
            "weight_hard_brake": AGGRESSION_WEIGHT_HARD_BRAKE,
            "weight_hard_acceleration": AGGRESSION_WEIGHT_HARD_ACCELERATION,
            "weight_overspeed": AGGRESSION_WEIGHT_OVERSPEED,
            "max_density": AGGRESSION_MAX_DENSITY,
        },
        "efficiency": {
            "max_events_per_km": EFFICIENCY_MAX_EVENTS_PER_KM,
        },
    }
