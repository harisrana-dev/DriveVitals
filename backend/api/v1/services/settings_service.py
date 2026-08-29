"""Settings service — persistence, defaults, and configuration retrieval.

Loads persisted settings from the database, falls back to application
defaults when no configuration has been saved, and persists admin updates.
"""

from dataclasses import dataclass

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
    DEFAULT_HEALTH_CONFIG,
    health_config_to_dict,
)
from backend.api.v1.schemas.settings import (
    AccountInfo,
    AggressionSettings,
    AnalyticsSettings,
    BrakeThresholdsSettings,
    CoolingThresholdsSettings,
    DriverStatisticsSettings,
    EfficiencySettings,
    EngineThresholdsSettings,
    FuelSystemThresholdsSettings,
    SafetySettings,
    StatusThresholdsSettings,
    SystemInfo,
    TransmissionThresholdsSettings,
    VehicleHealthSettings,
)
from backend.db.models.user import User
from backend.db.repositories.system_settings_repository import (
    SystemSettingsRepository,
)

# ---------------------------------------------------------------------------
# Valid category names
# ---------------------------------------------------------------------------

VALID_CATEGORIES = frozenset({"analytics"})

# ---------------------------------------------------------------------------
# Default analytics settings (derived from current application constants)
# ---------------------------------------------------------------------------


def _default_vehicle_health() -> VehicleHealthSettings:
    """Build VehicleHealthSettings from the existing DEFAULT_HEALTH_CONFIG."""
    from backend.analytics.vehicle_health.models.subsystem_health import Subsystem

    cfg = DEFAULT_HEALTH_CONFIG
    return VehicleHealthSettings(
        status=StatusThresholdsSettings(
            healthy_min=cfg.status.healthy_min,
            warning_min=cfg.status.warning_min,
        ),
        window_size=cfg.window_size,
        engine=EngineThresholdsSettings(**{
            k: getattr(cfg.engine, k)
            for k in EngineThresholdsSettings.model_fields
        }),
        brake=BrakeThresholdsSettings(**{
            k: getattr(cfg.brake, k)
            for k in BrakeThresholdsSettings.model_fields
        }),
        cooling=CoolingThresholdsSettings(**{
            k: getattr(cfg.cooling, k)
            for k in CoolingThresholdsSettings.model_fields
        }),
        transmission=TransmissionThresholdsSettings(**{
            k: getattr(cfg.transmission, k)
            for k in TransmissionThresholdsSettings.model_fields
        }),
        fuel_system=FuelSystemThresholdsSettings(**{
            k: getattr(cfg.fuel_system, k)
            for k in FuelSystemThresholdsSettings.model_fields
        }),
        weights={
            subsystem.value: weight
            for subsystem, weight in cfg.weights.items()
        },
    )


def _default_driver_statistics() -> DriverStatisticsSettings:
    """Build DriverStatisticsSettings from existing config constants."""
    return DriverStatisticsSettings(
        safety=SafetySettings(
            weight_hard_brake=SAFETY_WEIGHT_HARD_BRAKE,
            weight_hard_acceleration=SAFETY_WEIGHT_HARD_ACCELERATION,
            weight_overspeed=SAFETY_WEIGHT_OVERSPEED,
            weight_high_rpm=SAFETY_WEIGHT_HIGH_RPM,
            density_sensitivity=SAFETY_DENSITY_SENSITIVITY,
        ),
        aggression=AggressionSettings(
            weight_hard_brake=AGGRESSION_WEIGHT_HARD_BRAKE,
            weight_hard_acceleration=AGGRESSION_WEIGHT_HARD_ACCELERATION,
            weight_overspeed=AGGRESSION_WEIGHT_OVERSPEED,
            max_density=AGGRESSION_MAX_DENSITY,
        ),
        efficiency=EfficiencySettings(
            max_events_per_km=EFFICIENCY_MAX_EVENTS_PER_KM,
        ),
    )


def default_analytics_settings() -> AnalyticsSettings:
    """Return the default analytics configuration."""
    return AnalyticsSettings(
        vehicle_health=_default_vehicle_health(),
        driver_statistics=_default_driver_statistics(),
    )


# ---------------------------------------------------------------------------
# Settings service
# ---------------------------------------------------------------------------


class SettingsService:
    """Admin configuration service."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = SystemSettingsRepository(session)

    async def get_full_settings(
        self, user: User, uptime_seconds: int = 0
    ) -> dict:
        """Return the complete settings payload."""
        analytics = await self._get_analytics()

        return {
            "account": AccountInfo(
                user_id=user.user_id,
                email=user.email,
                full_name=user.full_name,
                role=user.role,
            ).model_dump(),
            "system": SystemInfo(
                uptime_seconds=uptime_seconds,
            ).model_dump(),
            "analytics": analytics.model_dump(),
        }

    async def get_category(
        self, category: str, uptime_seconds: int = 0
    ) -> dict | None:
        """Return a single settings category, or None if unknown."""
        if category not in VALID_CATEGORIES:
            return None

        if category == "analytics":
            analytics = await self._get_analytics()
            return {
                "category": "analytics",
                "data": analytics.model_dump(),
            }
        return None

    async def update_category(
        self,
        category: str,
        patch_data: dict,
        user: User,
    ) -> dict | None:
        """Validate and persist a configuration category update."""
        if category not in VALID_CATEGORIES:
            return None

        if category == "analytics":
            return await self._update_analytics(patch_data, user)

        return None

    # ----- internal helpers -----

    async def _get_analytics(self) -> AnalyticsSettings:
        """Load persisted analytics settings or return defaults."""
        row = await self._repo.get("analytics")
        if row is not None:
            try:
                return AnalyticsSettings(**row.settings_data)
            except Exception:
                pass
        return default_analytics_settings()

    async def _update_analytics(
        self, patch_data: dict, user: User
    ) -> dict:
        """Merge patch into current analytics settings and persist."""
        current = await self._get_analytics()

        # Deep merge: apply patch fields onto current values
        merged = current.model_dump()
        for key, value in patch_data.items():
            if value is None:
                continue
            if isinstance(value, dict) and isinstance(merged.get(key), dict):
                merged[key] = {**merged[key], **value}
            else:
                merged[key] = value

        # Validate the merged result
        validated = AnalyticsSettings(**merged)

        # Persist
        await self._repo.upsert(
            category="analytics",
            settings_data=validated.model_dump(),
            updated_by=user.user_id,
        )
        await self._session.commit()

        return {
            "category": "analytics",
            "data": validated.model_dump(),
        }
