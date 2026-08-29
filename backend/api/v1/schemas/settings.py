"""Settings schemas for the M3 admin configuration console.

Typed Pydantic models that represent real DriveVitals configuration.
Account and system sections are read-only.  Analytics is editable.
"""

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Account (read-only)
# ---------------------------------------------------------------------------


class AccountInfo(BaseModel):
    """Authenticated administrator's identity — read-only."""

    user_id: str
    email: str
    full_name: str
    role: str


# ---------------------------------------------------------------------------
# System (read-only)
# ---------------------------------------------------------------------------


class SystemInfo(BaseModel):
    """Runtime information — read-only."""

    app_name: str = "DriveVitals"
    version: str = "1.0.0"
    api_version: str = "v1"
    uptime_seconds: int = 0
    database_status: str = "connected"
    runtime_status: str = "operational"


# ---------------------------------------------------------------------------
# Vehicle Health settings
# ---------------------------------------------------------------------------


class StatusThresholdsSettings(BaseModel):
    healthy_min: float = Field(default=90.0, ge=0, le=100)
    warning_min: float = Field(default=70.0, ge=0, le=100)


class EngineThresholdsSettings(BaseModel):
    redline_rpm: float = Field(default=6200.0, gt=0)
    redline_deduction: float = Field(default=30.0, ge=0)
    sustained_rpm: float = Field(default=4500.0, gt=0)
    sustained_rpm_fraction: float = Field(default=0.30, ge=0, le=1)
    sustained_rpm_deduction: float = Field(default=25.0, ge=0)
    overheat_temp_c: float = Field(default=105.0, gt=0)
    overheat_span_c: float = Field(default=15.0, gt=0)
    overheat_deduction: float = Field(default=25.0, ge=0)
    max_load_percent: float = Field(default=85.0, ge=0, le=100)
    max_load_fraction: float = Field(default=0.40, ge=0, le=1)
    max_load_deduction: float = Field(default=25.0, ge=0)
    throttle_abuse_percent: float = Field(default=90.0, ge=0, le=100)
    throttle_abuse_fraction: float = Field(default=0.30, ge=0, le=1)
    throttle_abuse_deduction: float = Field(default=20.0, ge=0)
    aggressive_throttle_event_deduction: float = Field(default=4.0, ge=0)
    aggressive_throttle_event_cap: int = Field(default=4, ge=0)


class BrakeThresholdsSettings(BaseModel):
    harsh_brake_pressure: float = Field(default=0.80, ge=0, le=1)
    harsh_pressure_deduction: float = Field(default=10.0, ge=0)
    hard_brake_pressure: float = Field(default=0.60, ge=0, le=1)
    hard_brake_fraction: float = Field(default=0.25, ge=0, le=1)
    hard_brake_deduction: float = Field(default=15.0, ge=0)
    harsh_brake_event_deduction: float = Field(default=8.0, ge=0)
    harsh_brake_event_cap: int = Field(default=5, ge=0)


class CoolingThresholdsSettings(BaseModel):
    overheat_temp_c: float = Field(default=100.0, gt=0)
    overheat_span_c: float = Field(default=15.0, gt=0)
    overheat_deduction: float = Field(default=40.0, ge=0)
    elevated_temp_c: float = Field(default=90.0, gt=0)
    elevated_span_c: float = Field(default=10.0, gt=0)
    elevated_deduction: float = Field(default=10.0, ge=0)
    stability_stddev_c: float = Field(default=3.0, ge=0)
    stability_span_c: float = Field(default=10.0, gt=0)
    stability_deduction: float = Field(default=15.0, ge=0)
    max_load_percent: float = Field(default=85.0, ge=0, le=100)
    max_load_deduction: float = Field(default=10.0, ge=0)


class TransmissionThresholdsSettings(BaseModel):
    low_speed_kmh: float = Field(default=30.0, ge=0)
    stress_rpm: float = Field(default=4500.0, gt=0)
    stress_throttle_percent: float = Field(default=70.0, ge=0, le=100)
    stress_deduction: float = Field(default=20.0, ge=0)
    stress_fraction: float = Field(default=0.20, ge=0, le=1)
    stress_fraction_deduction: float = Field(default=25.0, ge=0)


class FuelSystemThresholdsSettings(BaseModel):
    min_speed_kmh: float = Field(default=25.0, ge=0)
    normal_load_min_percent: float = Field(default=20.0, ge=0, le=100)
    normal_load_max_percent: float = Field(default=70.0, ge=0, le=100)
    min_efficiency_km_per_l: float = Field(default=6.0, gt=0)
    efficiency_deduction: float = Field(default=30.0, ge=0)
    high_fuel_rate_lph: float = Field(default=25.0, gt=0)
    high_consumption_fraction: float = Field(default=0.15, ge=0, le=1)
    high_consumption_deduction: float = Field(default=15.0, ge=0)
    abuse_throttle_percent: float = Field(default=85.0, ge=0, le=100)
    abuse_deduction: float = Field(default=5.0, ge=0)


class VehicleHealthSettings(BaseModel):
    """Vehicle health configuration — editable by admin."""

    status: StatusThresholdsSettings = Field(default_factory=StatusThresholdsSettings)
    window_size: int = Field(default=20, ge=1, le=200)
    engine: EngineThresholdsSettings = Field(default_factory=EngineThresholdsSettings)
    brake: BrakeThresholdsSettings = Field(default_factory=BrakeThresholdsSettings)
    cooling: CoolingThresholdsSettings = Field(default_factory=CoolingThresholdsSettings)
    transmission: TransmissionThresholdsSettings = Field(default_factory=TransmissionThresholdsSettings)
    fuel_system: FuelSystemThresholdsSettings = Field(default_factory=FuelSystemThresholdsSettings)
    weights: dict[str, float] = Field(
        default_factory=lambda: {
            "engine": 0.30,
            "cooling": 0.20,
            "brakes": 0.20,
            "transmission": 0.15,
            "fuel_system": 0.15,
        }
    )

    @field_validator("weights")
    @classmethod
    def validate_weights(cls, v: dict[str, float]) -> dict[str, float]:
        for key, val in v.items():
            if val < 0:
                raise ValueError(f"Weight for '{key}' must be non-negative")
        total = sum(v.values())
        if abs(total - 1.0) > 0.01:
            raise ValueError(
                f"Subsystem weights must sum to 1.0 (got {total:.3f})"
            )
        return v


# ---------------------------------------------------------------------------
# Driver Statistics settings
# ---------------------------------------------------------------------------


class SafetySettings(BaseModel):
    weight_hard_brake: float = Field(default=2.0, ge=0)
    weight_hard_acceleration: float = Field(default=1.5, ge=0)
    weight_overspeed: float = Field(default=3.0, ge=0)
    weight_high_rpm: float = Field(default=1.0, ge=0)
    density_sensitivity: float = Field(default=0.35, ge=0)


class AggressionSettings(BaseModel):
    weight_hard_brake: float = Field(default=2.0, ge=0)
    weight_hard_acceleration: float = Field(default=1.5, ge=0)
    weight_overspeed: float = Field(default=3.0, ge=0)
    max_density: float = Field(default=1.0, gt=0)


class EfficiencySettings(BaseModel):
    max_events_per_km: float = Field(default=1.0, gt=0)


class DriverStatisticsSettings(BaseModel):
    """Driver statistics configuration — editable by admin."""

    safety: SafetySettings = Field(default_factory=SafetySettings)
    aggression: AggressionSettings = Field(default_factory=AggressionSettings)
    efficiency: EfficiencySettings = Field(default_factory=EfficiencySettings)


# ---------------------------------------------------------------------------
# Analytics (composed)
# ---------------------------------------------------------------------------


class AnalyticsSettings(BaseModel):
    """Analytics configuration — composed of sub-sections."""

    vehicle_health: VehicleHealthSettings = Field(
        default_factory=VehicleHealthSettings
    )
    driver_statistics: DriverStatisticsSettings = Field(
        default_factory=DriverStatisticsSettings
    )


# ---------------------------------------------------------------------------
# PATCH schemas
# ---------------------------------------------------------------------------


class VehicleHealthPatch(BaseModel):
    """Partial update for vehicle health settings."""

    status: StatusThresholdsSettings | None = None
    window_size: int | None = Field(default=None, ge=1, le=200)
    engine: EngineThresholdsSettings | None = None
    brake: BrakeThresholdsSettings | None = None
    cooling: CoolingThresholdsSettings | None = None
    transmission: TransmissionThresholdsSettings | None = None
    fuel_system: FuelSystemThresholdsSettings | None = None
    weights: dict[str, float] | None = None

    @field_validator("weights")
    @classmethod
    def validate_weights(cls, v: dict[str, float] | None) -> dict[str, float] | None:
        if v is None:
            return v
        for key, val in v.items():
            if val < 0:
                raise ValueError(f"Weight for '{key}' must be non-negative")
        total = sum(v.values())
        if abs(total - 1.0) > 0.01:
            raise ValueError(
                f"Subsystem weights must sum to 1.0 (got {total:.3f})"
            )
        return v


class DriverStatisticsPatch(BaseModel):
    """Partial update for driver statistics settings."""

    safety: SafetySettings | None = None
    aggression: AggressionSettings | None = None
    efficiency: EfficiencySettings | None = None


class AnalyticsPatch(BaseModel):
    """Partial update for analytics settings."""

    vehicle_health: VehicleHealthPatch | None = None
    driver_statistics: DriverStatisticsPatch | None = None


# ---------------------------------------------------------------------------
# Full Settings payload
# ---------------------------------------------------------------------------


class SettingsPayload(BaseModel):
    """Complete admin settings payload returned by GET /settings."""

    account: AccountInfo
    system: SystemInfo
    analytics: AnalyticsSettings


# ---------------------------------------------------------------------------
# Category-specific response models
# ---------------------------------------------------------------------------


class SettingsCategoryResponse(BaseModel):
    """Response for a single settings category."""

    category: str
    data: dict
