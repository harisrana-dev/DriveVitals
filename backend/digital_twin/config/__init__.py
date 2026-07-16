"""Configuration Layer for the DriveVitals Digital Twin.

Public surface:
    - `constants`: system-wide default values (module, imported as-is).
    - `simulation_config`: frozen dataclasses for every subsystem config.
    - `defaults`: factory functions returning ready-to-use configs.

External (file-based) configuration loading is intentionally not part
of this layer yet; configuration objects are constructed directly in
Python via `defaults.create_default_simulation_config()` or by
instantiating the dataclasses in `simulation_config` directly.
"""

from __future__ import annotations

from digital_twin.config.defaults import create_default_simulation_config
from digital_twin.config.simulation_config import (
    AnalyticsConfig,
    ClockConfig,
    DriverConfig,
    DriverManagerConfig,
    EnvironmentManagerConfig,
    FleetConfig,
    FleetManagerConfig,
    MaintenanceManagerConfig,
    SimulationConfig,
    TelemetryConfig,
    TripConfig,
    VehicleConfig,
)

__all__ = [
    "AnalyticsConfig",
    "ClockConfig",
    "DriverConfig",
    "DriverManagerConfig",
    "EnvironmentManagerConfig",
    "FleetConfig",
    "FleetManagerConfig",
    "MaintenanceManagerConfig",
    "SimulationConfig",
    "TelemetryConfig",
    "TripConfig",
    "VehicleConfig",
    "create_default_simulation_config",
]