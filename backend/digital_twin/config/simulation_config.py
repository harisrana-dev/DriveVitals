"""Configuration objects for the Digital Twin simulation.

This module is the complete Configuration Layer for Sprint 1. All
objects here are plain, frozen dataclasses: configuration values only,
no runtime logic, no I/O, no file/YAML/JSON parsing (that is explicitly
deferred to a later sprint). Every value defaults from `constants.py`
so there is exactly one place to change a system-wide default.

Backward compatibility note:
    `ClockConfig`, `FleetManagerConfig`, `DriverManagerConfig`,
    `MaintenanceManagerConfig`, `EnvironmentManagerConfig`, and
    `SimulationConfig` are the exact names and field shapes already
    imported by the existing Runtime and Manager modules
    (`digital_twin_runtime.py`, `simulation_clock.py`,
    `fleet_manager.py`, `driver_manager.py`,
    `maintenance_manager.py`, `environment_manager.py`). Those names
    and their fields are unchanged here so existing imports keep
    working without touching Runtime or Manager code.

    `FleetConfig` and `DriverConfig` are provided as aliases of
    `FleetManagerConfig` / `DriverManagerConfig` so both naming
    conventions resolve to the same type. `VehicleConfig`,
    `TripConfig`, `TelemetryConfig`, and `AnalyticsConfig` are new,
    forward-looking subsystem configs for domains that don't have a
    manager consuming them yet (Vehicle/Trip entity behavior,
    Telemetry, Analytics are future sprints); they are included on
    `SimulationConfig` now so the aggregate is complete, with safe
    defaults that do not affect Sprint 1 behavior.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from digital_twin.common.exceptions import ConfigurationError
from digital_twin.config import constants


@dataclass(frozen=True)
class ClockConfig:
    """Configuration for the SimulationClock.

    Attributes:
        tick_interval_seconds: Real-world seconds between ticks when the
            runtime drives the clock in real time.
        simulated_seconds_per_tick: How many simulated seconds elapse per
            tick at 1x clock speed.
        initial_clock_speed: Multiplier applied to simulated time per
            tick (e.g. 60.0 => 1 real second == 1 simulated minute).
    """

    tick_interval_seconds: float = constants.DEFAULT_TICK_INTERVAL_SECONDS
    simulated_seconds_per_tick: float = constants.DEFAULT_SIMULATED_SECONDS_PER_TICK
    initial_clock_speed: float = constants.DEFAULT_CLOCK_SPEED

    def __post_init__(self) -> None:
        """Validate invariants.

        Raises:
            ConfigurationError: If any value is non-positive.
        """
        if self.tick_interval_seconds <= 0:
            raise ConfigurationError("tick_interval_seconds must be positive.")
        if self.simulated_seconds_per_tick <= 0:
            raise ConfigurationError("simulated_seconds_per_tick must be positive.")
        if self.initial_clock_speed <= 0:
            raise ConfigurationError("initial_clock_speed must be positive.")


@dataclass(frozen=True)
class FleetManagerConfig:
    """Configuration for FleetManager.

    Attributes:
        max_vehicles: Maximum number of vehicles the fleet may register.
        max_drivers: Maximum number of drivers the fleet may register.
    """

    max_vehicles: int = constants.MAX_FLEET_SIZE
    max_drivers: int = constants.MAX_DRIVER_COUNT


@dataclass(frozen=True)
class DriverManagerConfig:
    """Configuration for DriverManager.

    Attributes:
        max_working_hours_per_shift: Max continuous working hours before
            a driver is forced into a break/fatigue state.
        mandatory_break_minutes: Minimum break duration in minutes once
            triggered.
        fatigue_threshold_hours: Hours of continuous work after which a
            driver is flagged FATIGUED.
    """

    max_working_hours_per_shift: float = constants.DEFAULT_MAX_WORKING_HOURS_PER_SHIFT
    mandatory_break_minutes: float = constants.DEFAULT_MANDATORY_BREAK_MINUTES
    fatigue_threshold_hours: float = constants.DEFAULT_FATIGUE_THRESHOLD_HOURS


@dataclass(frozen=True)
class VehicleConfig:
    """Configuration for vehicle-related defaults.

    Not yet consumed by VehicleManager in Sprint 1 (which takes no
    configuration today); included so SimulationConfig is a complete
    aggregate and future sprints (Entities/Physics) have a home for
    vehicle-level defaults without changing SimulationConfig's shape.

    Attributes:
        default_service_interval_km: Default distance, in km, between
            scheduled services for a newly onboarded vehicle.
    """

    default_service_interval_km: float = constants.DEFAULT_SERVICE_INTERVAL_KM


@dataclass(frozen=True)
class TripConfig:
    """Configuration for trip-related defaults.

    Not yet consumed by TripManager in Sprint 1 (which takes no
    configuration today); included so SimulationConfig is a complete
    aggregate for future sprints.

    Attributes:
        max_active_trips: Maximum number of trips a fleet may hold
            active (non-terminal) at once.
    """

    max_active_trips: int = constants.DEFAULT_MAX_ACTIVE_TRIPS


@dataclass(frozen=True)
class MaintenanceManagerConfig:
    """Configuration for MaintenanceManager.

    Attributes:
        due_soon_mileage_threshold_km: Distance (km) remaining before a
            scheduled service at which status becomes DUE_SOON.
        inspection_interval_days: Days between mandatory inspections.
    """

    due_soon_mileage_threshold_km: float = (
        constants.DEFAULT_DUE_SOON_MILEAGE_THRESHOLD_KM
    )
    inspection_interval_days: int = constants.DEFAULT_INSPECTION_INTERVAL_DAYS


@dataclass(frozen=True)
class EnvironmentManagerConfig:
    """Configuration for EnvironmentManager.

    Attributes:
        default_weather: Weather condition the simulation starts in.
        random_seed: Seed for environment-related randomness (variation
            only, never behavior-driving) per Digital Twin principles.
    """

    default_weather: str = constants.DEFAULT_WEATHER
    random_seed: int = constants.DEFAULT_ENVIRONMENT_RANDOM_SEED


@dataclass(frozen=True)
class TelemetryConfig:
    """Configuration for the future Telemetry subsystem.

    Not yet consumed by any Sprint 1 manager (Telemetry is a future
    sprint); included so SimulationConfig is a complete aggregate.

    Attributes:
        sampling_frequency_hz: Default telemetry sampling frequency.
        buffer_size: Number of samples retained in memory per vehicle.
    """

    sampling_frequency_hz: float = constants.DEFAULT_TELEMETRY_FREQUENCY_HZ
    buffer_size: int = constants.DEFAULT_TELEMETRY_BUFFER_SIZE

    def __post_init__(self) -> None:
        """Validate invariants.

        Raises:
            ConfigurationError: If sampling_frequency_hz is non-positive
                or exceeds the platform-wide maximum.
        """
        if self.sampling_frequency_hz <= 0:
            raise ConfigurationError("sampling_frequency_hz must be positive.")
        if self.sampling_frequency_hz > constants.MAX_TELEMETRY_FREQUENCY_HZ:
            raise ConfigurationError(
                "sampling_frequency_hz exceeds MAX_TELEMETRY_FREQUENCY_HZ "
                f"({constants.MAX_TELEMETRY_FREQUENCY_HZ})."
            )


@dataclass(frozen=True)
class AnalyticsConfig:
    """Configuration for the future Analytics subsystem.

    Not yet consumed by any Sprint 1 manager (Analytics is a future
    sprint); included so SimulationConfig is a complete aggregate.

    Attributes:
        window_minutes: Rolling window, in simulated minutes, used by
            analytics aggregates when no explicit window is given.
        refresh_ticks: Number of ticks between analytics recomputation.
    """

    window_minutes: float = constants.DEFAULT_ANALYTICS_WINDOW_MINUTES
    refresh_ticks: int = constants.DEFAULT_ANALYTICS_REFRESH_TICKS


@dataclass(frozen=True)
class SimulationConfig:
    """Top-level configuration aggregate injected into DigitalTwinRuntime.

    Attributes:
        clock: Clock configuration.
        fleet: FleetManager configuration.
        driver: DriverManager configuration.
        vehicle: Vehicle-domain configuration (not yet consumed by a
            manager in Sprint 1; reserved for future sprints).
        trip: Trip-domain configuration (not yet consumed by a manager
            in Sprint 1; reserved for future sprints).
        maintenance: MaintenanceManager configuration.
        environment: EnvironmentManager configuration.
        telemetry: Telemetry-domain configuration (not yet consumed;
            reserved for a future sprint).
        analytics: Analytics-domain configuration (not yet consumed;
            reserved for a future sprint).
    """

    clock: ClockConfig = field(default_factory=ClockConfig)
    fleet: FleetManagerConfig = field(default_factory=FleetManagerConfig)
    driver: DriverManagerConfig = field(default_factory=DriverManagerConfig)
    vehicle: VehicleConfig = field(default_factory=VehicleConfig)
    trip: TripConfig = field(default_factory=TripConfig)
    maintenance: MaintenanceManagerConfig = field(
        default_factory=MaintenanceManagerConfig
    )
    environment: EnvironmentManagerConfig = field(
        default_factory=EnvironmentManagerConfig
    )
    telemetry: TelemetryConfig = field(default_factory=TelemetryConfig)
    analytics: AnalyticsConfig = field(default_factory=AnalyticsConfig)


# --- Naming-convention aliases ---------------------------------------------
#
# The Sprint requirements list "FleetConfig" and "DriverConfig" as the
# expected subsystem config names. The existing Runtime/Manager code
# already imports "FleetManagerConfig" / "DriverManagerConfig" (see the
# module docstring above), so those remain the canonical classes and
# these are plain aliases -- both names resolve to the identical type,
# and no manager code needed to change.
FleetConfig = FleetManagerConfig
DriverConfig = DriverManagerConfig