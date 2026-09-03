"""Pydantic schemas for the Digital Twin Lab (admin-only).

Mirrors the persisted simulation domain (drivers, vehicles, routes,
assignments, scenarios, runs) plus the live simulation controller
status. Read schemas are validated from ORM attributes; write schemas
carry the strictly-validated payloads accepted by the admin API.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Drivers
# ---------------------------------------------------------------------------

class DriverManagementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    driver_id: str
    first_name: str
    last_name: str
    license_number: str
    employment_status: str
    behavior_profile: str
    created_at: datetime
    updated_at: datetime


class DriverCreate(BaseModel):
    driver_id: str | None = None
    first_name: str = Field(min_length=1, max_length=50)
    last_name: str = Field(min_length=0, max_length=50)
    license_number: str = Field(min_length=1, max_length=30)
    employment_status: str = "active"
    behavior_profile: str = "standard"


class DriverUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=50)
    last_name: str | None = Field(default=None, max_length=50)
    license_number: str | None = Field(default=None, max_length=30)
    employment_status: str | None = None
    behavior_profile: str | None = None


# ---------------------------------------------------------------------------
# Vehicles
# ---------------------------------------------------------------------------

class VehicleManagementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    vehicle_id: str
    registration_number: str
    vin: str
    manufacturer: str
    model: str
    year: int
    fuel_type: str
    status: str
    display_name: str | None = None
    fuel_efficiency_factor: float
    acceleration_response: float
    tank_capacity_liters: float
    created_at: datetime
    updated_at: datetime


class VehicleCreate(BaseModel):
    vehicle_id: str | None = None
    registration_number: str = Field(min_length=1, max_length=50)
    vin: str = Field(min_length=1, max_length=17)
    manufacturer: str = Field(min_length=1, max_length=50)
    model: str = Field(min_length=1, max_length=50)
    year: int = Field(ge=1980, le=2100)
    fuel_type: str = "diesel"
    status: str = "active"
    display_name: str | None = Field(default=None, max_length=100)
    fuel_efficiency_factor: float = Field(default=1.0, ge=0.4, le=2.5)
    acceleration_response: float = Field(default=1.0, ge=0.4, le=2.5)
    tank_capacity_liters: float = Field(default=60.0, ge=20.0, le=200.0)


class VehicleUpdate(BaseModel):
    registration_number: str | None = Field(default=None, max_length=50)
    vin: str | None = Field(default=None, max_length=17)
    manufacturer: str | None = Field(default=None, max_length=50)
    model: str | None = Field(default=None, max_length=50)
    year: int | None = Field(default=None, ge=1980, le=2100)
    fuel_type: str | None = None
    status: str | None = None
    display_name: str | None = Field(default=None, max_length=100)
    fuel_efficiency_factor: float | None = Field(default=None, ge=0.4, le=2.5)
    acceleration_response: float | None = Field(default=None, ge=0.4, le=2.5)
    tank_capacity_liters: float | None = Field(default=None, ge=20.0, le=200.0)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

class RouteManagementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    route_id: str
    name: str
    route_type: str
    origin: str
    destination: str
    estimated_distance_km: float
    speed_limit_kmh: float
    is_active: bool
    created_at: datetime
    updated_at: datetime


class RouteCreate(BaseModel):
    route_id: str | None = None
    name: str = Field(min_length=1, max_length=100)
    route_type: str = "urban"
    origin: str = Field(min_length=1)
    destination: str = Field(min_length=1)
    estimated_distance_km: float = Field(gt=0, le=10000.0)
    speed_limit_kmh: float = Field(default=60.0, gt=0, le=200.0)
    is_active: bool = True


class RouteUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    route_type: str | None = None
    origin: str | None = None
    destination: str | None = None
    estimated_distance_km: float | None = Field(default=None, gt=0, le=10000.0)
    speed_limit_kmh: float | None = Field(default=None, gt=0, le=200.0)
    is_active: bool | None = None


# ---------------------------------------------------------------------------
# Assignments
# ---------------------------------------------------------------------------

class AssignmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    assignment_id: str
    driver_id: str
    vehicle_id: str
    route_id: str
    name: str | None = None
    notes: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class AssignmentCreate(BaseModel):
    assignment_id: str | None = None
    driver_id: str = Field(min_length=1)
    vehicle_id: str = Field(min_length=1)
    route_id: str = Field(min_length=1)
    name: str | None = Field(default=None, max_length=100)
    notes: str | None = None
    is_active: bool = True


class AssignmentUpdate(BaseModel):
    driver_id: str | None = None
    vehicle_id: str | None = None
    route_id: str | None = None
    name: str | None = Field(default=None, max_length=100)
    notes: str | None = None
    is_active: bool | None = None


# ---------------------------------------------------------------------------
# Scenarios & runs
# ---------------------------------------------------------------------------

class ScenarioRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    scenario_id: str
    name: str
    description: str | None = None
    status: str
    duration_seconds: int | None = None
    simulation_speed: float
    seed: int | None = None
    created_at: datetime
    updated_at: datetime


class ScenarioCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = None
    status: str = "draft"
    duration_seconds: int | None = Field(default=None, gt=0, le=86400 * 7)
    simulation_speed: float = Field(default=1.0, ge=0.1, le=100.0)
    seed: int | None = None


class ScenarioUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None
    status: str | None = None
    duration_seconds: int | None = Field(default=None, gt=0, le=86400 * 7)
    simulation_speed: float | None = Field(default=None, ge=0.1, le=100.0)
    seed: int | None = None


class RunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    run_id: str
    scenario_id: str
    status: str
    seed: int | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    vehicles_active: int
    trips_completed: int
    error: str | None = None
    created_at: datetime | None = None


# ---------------------------------------------------------------------------
# Simulation controller status
# ---------------------------------------------------------------------------

class SimulationStatus(BaseModel):
    running: bool
    scenario_id: str | None = None
    scenario_name: str | None = None
    run_id: str | None = None
    started_at: datetime | None = None
    vehicles: int = 0
