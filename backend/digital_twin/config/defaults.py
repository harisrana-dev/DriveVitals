"""Factory functions for default Digital Twin configuration.

These are plain factory functions -- no file/YAML/JSON parsing, no I/O,
no logic beyond constructing dataclasses. They exist so the Runtime and
managers can be started for development/testing purely in Python,
without hand-assembling every subsystem config at every call site.
External (file-based) configuration loading is an explicit non-goal of
this sprint and is deferred to a later one.
"""

from __future__ import annotations

from digital_twin.config.simulation_config import (
    AnalyticsConfig,
    ClockConfig,
    DriverManagerConfig,
    EnvironmentManagerConfig,
    FleetManagerConfig,
    MaintenanceManagerConfig,
    SimulationConfig,
    TelemetryConfig,
    TripConfig,
    VehicleConfig,
)


def create_default_clock_config() -> ClockConfig:
    """Create a ClockConfig using system-wide defaults.

    Returns:
        A ClockConfig with default tick interval, seconds-per-tick, and
        clock speed.
    """
    return ClockConfig()


def create_default_fleet_config() -> FleetManagerConfig:
    """Create a FleetManagerConfig using system-wide defaults.

    Returns:
        A FleetManagerConfig with default fleet/driver capacity limits.
    """
    return FleetManagerConfig()


def create_default_driver_config() -> DriverManagerConfig:
    """Create a DriverManagerConfig using system-wide defaults.

    Returns:
        A DriverManagerConfig with default working-hour, break, and
        fatigue thresholds.
    """
    return DriverManagerConfig()


def create_default_vehicle_config() -> VehicleConfig:
    """Create a VehicleConfig using system-wide defaults.

    Returns:
        A VehicleConfig with the default service interval.
    """
    return VehicleConfig()


def create_default_trip_config() -> TripConfig:
    """Create a TripConfig using system-wide defaults.

    Returns:
        A TripConfig with the default max active trip count.
    """
    return TripConfig()


def create_default_maintenance_config() -> MaintenanceManagerConfig:
    """Create a MaintenanceManagerConfig using system-wide defaults.

    Returns:
        A MaintenanceManagerConfig with default mileage/inspection
        thresholds.
    """
    return MaintenanceManagerConfig()


def create_default_environment_config() -> EnvironmentManagerConfig:
    """Create an EnvironmentManagerConfig using system-wide defaults.

    Returns:
        An EnvironmentManagerConfig with the default starting weather
        and random seed.
    """
    return EnvironmentManagerConfig()


def create_default_telemetry_config() -> TelemetryConfig:
    """Create a TelemetryConfig using system-wide defaults.

    Returns:
        A TelemetryConfig with the default sampling frequency and
        buffer size.
    """
    return TelemetryConfig()


def create_default_analytics_config() -> AnalyticsConfig:
    """Create an AnalyticsConfig using system-wide defaults.

    Returns:
        An AnalyticsConfig with the default rolling window and refresh
        interval.
    """
    return AnalyticsConfig()


def create_default_simulation_config() -> SimulationConfig:
    """Create a fully initialized SimulationConfig for dev/test use.

    This is the single call a composition root needs to get the
    Digital Twin runnable with no external files: every subsystem
    config is populated with system-wide defaults from
    `constants.py`.

    Returns:
        A complete SimulationConfig ready to pass into
        DigitalTwinRuntime and, for each subsystem, its corresponding
        manager (e.g. `config.driver` into `DriverManager`).
    """
    return SimulationConfig(
        clock=create_default_clock_config(),
        fleet=create_default_fleet_config(),
        driver=create_default_driver_config(),
        vehicle=create_default_vehicle_config(),
        trip=create_default_trip_config(),
        maintenance=create_default_maintenance_config(),
        environment=create_default_environment_config(),
        telemetry=create_default_telemetry_config(),
        analytics=create_default_analytics_config(),
    )