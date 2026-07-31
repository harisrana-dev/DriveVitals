"""
Maintenance configuration.

Central home for every constant used by the Maintenance subsystem:

    * remaining distance -> priority thresholds
    * subsystem health score -> severity thresholds
    * per-service intervals, costs and actions
    * engine operating thresholds used for stress detection

Constants must never be scattered across estimator modules. New knobs
are introduced here first and consumed through MaintenanceConfig.
"""

from dataclasses import dataclass, field

from backend.maintenance.models.maintenance_type import MaintenanceType


@dataclass(frozen=True, slots=True)
class PriorityThresholds:
    """
    Map a remaining distance to a MaintenancePriority.

    Remaining distance at or below a threshold falls into the level that
    threshold guards:

        remaining >  low_min  -> LOW
        medium < remaining <= low_min   -> MEDIUM
        high   < remaining <= medium_min -> HIGH
        remaining <= high_min           -> CRITICAL
    """

    low_min_km: float = 5000.0
    medium_min_km: float = 2000.0
    high_min_km: float = 500.0


@dataclass(frozen=True, slots=True)
class SeverityThresholds:
    """
    Map a subsystem health score to a MaintenanceSeverity.

    Mirrors the health score thresholds used by Vehicle Health so both
    layers classify a subsystem the same way.
    """

    minor_min_score: float = 90.0
    moderate_min_score: float = 70.0


@dataclass(frozen=True, slots=True)
class EngineOperatingThresholds:
    """
    Engine stress detection on the latest telemetry sample. Used to pull
    engine service intervals closer when the engine is currently running
    under sustained stress (overheating or above redline).
    """

    overheat_temp_c: float = 105.0
    redline_rpm: float = 6200.0
    stress_factor: float = 0.75


@dataclass(frozen=True, slots=True)
class ServiceProfile:
    """
    One service DriveVitals can recommend for a subsystem.

    interval_km is the service interval applied on a fully healthy
    subsystem. The interval shortens as subsystem health deteriorates.
    """

    maintenance_type: MaintenanceType
    label: str
    interval_km: float
    recommended_action: str
    estimated_cost: float | None = None


_ENGINE_SERVICES: tuple[ServiceProfile, ...] = (
    ServiceProfile(
        maintenance_type=MaintenanceType.OIL_CHANGE,
        label="Oil change",
        interval_km=10000.0,
        recommended_action="Replace engine oil and oil filter",
        estimated_cost=80.0,
    ),
    ServiceProfile(
        maintenance_type=MaintenanceType.ENGINE_INSPECTION,
        label="Engine inspection",
        interval_km=20000.0,
        recommended_action="Full engine inspection (belts, seals, compression)",
        estimated_cost=120.0,
    ),
    ServiceProfile(
        maintenance_type=MaintenanceType.SPARK_PLUG_SERVICE,
        label="Spark plug service",
        interval_km=40000.0,
        recommended_action="Replace spark plugs and inspect ignition system",
        estimated_cost=180.0,
    ),
)

_BRAKE_SERVICES: tuple[ServiceProfile, ...] = (
    ServiceProfile(
        maintenance_type=MaintenanceType.BRAKE_INSPECTION,
        label="Brake inspection",
        interval_km=10000.0,
        recommended_action="Inspect brake pads, discs, hoses and fluid level",
        estimated_cost=40.0,
    ),
    ServiceProfile(
        maintenance_type=MaintenanceType.BRAKE_PAD_REPLACEMENT,
        label="Brake pad replacement",
        interval_km=30000.0,
        recommended_action="Replace brake pads and inspect discs for wear",
        estimated_cost=250.0,
    ),
    ServiceProfile(
        maintenance_type=MaintenanceType.BRAKE_FLUID_SERVICE,
        label="Brake fluid service",
        interval_km=50000.0,
        recommended_action="Flush and replace brake fluid",
        estimated_cost=90.0,
    ),
)

_COOLING_SERVICES: tuple[ServiceProfile, ...] = (
    ServiceProfile(
        maintenance_type=MaintenanceType.COOLING_SYSTEM_INSPECTION,
        label="Cooling system inspection",
        interval_km=30000.0,
        recommended_action="Inspect cooling system hoses, thermostat and water pump",
        estimated_cost=60.0,
    ),
    ServiceProfile(
        maintenance_type=MaintenanceType.RADIATOR_INSPECTION,
        label="Radiator inspection",
        interval_km=50000.0,
        recommended_action="Inspect radiator for blockages and leaks",
        estimated_cost=70.0,
    ),
    ServiceProfile(
        maintenance_type=MaintenanceType.COOLANT_FLUSH,
        label="Coolant flush",
        interval_km=60000.0,
        recommended_action="Flush and replace engine coolant",
        estimated_cost=140.0,
    ),
)

_TRANSMISSION_SERVICES: tuple[ServiceProfile, ...] = (
    ServiceProfile(
        maintenance_type=MaintenanceType.TRANSMISSION_INSPECTION,
        label="Transmission inspection",
        interval_km=40000.0,
        recommended_action="Inspect transmission for leaks and abnormal wear",
        estimated_cost=80.0,
    ),
    ServiceProfile(
        maintenance_type=MaintenanceType.TRANSMISSION_SERVICE,
        label="Transmission service",
        interval_km=80000.0,
        recommended_action="Service transmission (fluid and filter)",
        estimated_cost=300.0,
    ),
)

_FUEL_SYSTEM_SERVICES: tuple[ServiceProfile, ...] = (
    ServiceProfile(
        maintenance_type=MaintenanceType.FUEL_FILTER_REPLACEMENT,
        label="Fuel filter replacement",
        interval_km=30000.0,
        recommended_action="Replace fuel filter",
        estimated_cost=110.0,
    ),
    ServiceProfile(
        maintenance_type=MaintenanceType.INJECTOR_CLEANING,
        label="Injector cleaning",
        interval_km=50000.0,
        recommended_action="Clean fuel injectors",
        estimated_cost=150.0,
    ),
    ServiceProfile(
        maintenance_type=MaintenanceType.FUEL_PUMP_INSPECTION,
        label="Fuel pump inspection",
        interval_km=80000.0,
        recommended_action="Inspect fuel pump pressure and strainer",
        estimated_cost=90.0,
    ),
)


@dataclass(frozen=True, slots=True)
class MaintenanceConfig:
    """
    Aggregate configuration for the Maintenance subsystem.
    """

    priority: PriorityThresholds = PriorityThresholds()
    severity: SeverityThresholds = SeverityThresholds()
    engine: EngineOperatingThresholds = EngineOperatingThresholds()

    # Assumed average daily distance used to project a due date from a
    # remaining distance. A configurable planning assumption.
    daily_distance_km: float = 100.0

    engine_services: tuple[ServiceProfile, ...] = field(
        default_factory=lambda: _ENGINE_SERVICES
    )
    brake_services: tuple[ServiceProfile, ...] = field(
        default_factory=lambda: _BRAKE_SERVICES
    )
    cooling_services: tuple[ServiceProfile, ...] = field(
        default_factory=lambda: _COOLING_SERVICES
    )
    transmission_services: tuple[ServiceProfile, ...] = field(
        default_factory=lambda: _TRANSMISSION_SERVICES
    )
    fuel_system_services: tuple[ServiceProfile, ...] = field(
        default_factory=lambda: _FUEL_SYSTEM_SERVICES
    )


DEFAULT_MAINTENANCE_CONFIG = MaintenanceConfig()


__all__ = [
    "PriorityThresholds",
    "SeverityThresholds",
    "EngineOperatingThresholds",
    "ServiceProfile",
    "MaintenanceConfig",
    "DEFAULT_MAINTENANCE_CONFIG",
]
