"""Shared enumerations used across the Digital Twin runtime and managers.

Centralizing enums here avoids duplicated definitions across manager
modules and prevents accidental drift between, e.g., two different
"VehicleStatus" enums defined in two different files.
"""

from __future__ import annotations

from enum import Enum, auto


class SimulationStatus(str, Enum):
    """Lifecycle state of the overall simulation."""

    STOPPED = "STOPPED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"


class VehicleStatus(str, Enum):
    """Current lifecycle/availability status of a vehicle."""

    AVAILABLE = "AVAILABLE"
    ASSIGNED = "ASSIGNED"
    ON_TRIP = "ON_TRIP"
    IN_MAINTENANCE = "IN_MAINTENANCE"
    OUT_OF_SERVICE = "OUT_OF_SERVICE"


class DriverStatus(str, Enum):
    """Current availability status of a driver."""

    OFF_DUTY = "OFF_DUTY"
    AVAILABLE = "AVAILABLE"
    ASSIGNED = "ASSIGNED"
    ON_TRIP = "ON_TRIP"
    ON_BREAK = "ON_BREAK"
    FATIGUED = "FATIGUED"


class TripStatus(str, Enum):
    """Lifecycle status of a trip."""

    PENDING = "PENDING"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class MaintenanceStatus(str, Enum):
    """Maintenance state of a vehicle."""

    OK = "OK"
    DUE_SOON = "DUE_SOON"
    OVERDUE = "OVERDUE"
    IN_PROGRESS = "IN_PROGRESS"


class WeatherCondition(str, Enum):
    """Simulated weather condition affecting driving conditions."""

    CLEAR = "CLEAR"
    RAIN = "RAIN"
    FOG = "FOG"
    SNOW = "SNOW"
    STORM = "STORM"


class RoadCondition(str, Enum):
    """Simulated road surface / event condition."""

    NORMAL = "NORMAL"
    CONGESTED = "CONGESTED"
    CONSTRUCTION = "CONSTRUCTION"
    ACCIDENT = "ACCIDENT"
    CLOSED = "CLOSED"


class ExecutionPhase(Enum):
    """Fixed execution phases processed in order on every tick.

    The scheduler iterates these phases in declaration order. Do not
    reorder members; the Digital Twin's execution order is a frozen
    architectural decision (Clock -> Environment -> Dispatch -> Drivers
    -> Vehicles -> Trips -> Maintenance).
    """

    ENVIRONMENT = auto()
    DISPATCH = auto()
    DRIVERS = auto()
    VEHICLES = auto()
    TRIPS = auto()
    MAINTENANCE = auto()