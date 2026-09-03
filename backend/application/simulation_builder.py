"""Build fleet runtime configurations from persisted simulation data.

The Digital Twin Lab stores its fleet (drivers, vehicles, routes) and the
assignments that compose a scenario in the database. These helpers map
those persisted ORM rows into the in-memory domain dataclasses that the
runtime (:class:`FleetRunner`) executes, preserving the simulation
characteristics (behavior profile, fuel-efficiency factor, acceleration
response, tank capacity, route speed limit) that drive telemetry
variability.

The existing read path (``fleet/config``) is untouched; this is a
parallel, persistence-driven source for scenario launches.
"""

import uuid

from backend.fleet.config.fleet_factory import FleetConfiguration
from backend.fleet.models.assignment import Assignment
from backend.fleet.models.driver import BehaviorProfile, Driver
from backend.fleet.models.route import Route, RouteType
from backend.fleet.models.vehicle import Vehicle

from backend.db.models.assignment import Assignment as PersistedAssignment
from backend.db.models.driver import Driver as PersistedDriver
from backend.db.models.route import Route as PersistedRoute
from backend.db.models.vehicle import Vehicle as PersistedVehicle


def _behavior_profile(value: str) -> BehaviorProfile:
    try:
        return BehaviorProfile(value)
    except ValueError:
        return BehaviorProfile.STANDARD


def _route_type(value: str) -> RouteType:
    try:
        return RouteType(value)
    except ValueError:
        return RouteType.URBAN


def to_domain_driver(row: PersistedDriver) -> Driver:
    name = f"{row.first_name} {row.last_name}".strip()
    return Driver(
        driver_id=row.driver_id,
        name=name,
        behavior_profile=_behavior_profile(row.behavior_profile),
    )


def to_domain_vehicle(row: PersistedVehicle) -> Vehicle:
    return Vehicle(
        vehicle_id=row.vehicle_id,
        make=row.manufacturer,
        model=row.model,
        year=row.year,
        fuel_efficiency_factor=row.fuel_efficiency_factor,
        acceleration_response=row.acceleration_response,
        tank_capacity_liters=row.tank_capacity_liters,
        display_name=row.display_name,
    )


def to_domain_route(row: PersistedRoute) -> Route:
    return Route(
        route_id=row.route_id,
        origin=row.origin,
        destination=row.destination,
        distance_km=row.estimated_distance_km,
        route_type=_route_type(row.route_type),
        speed_limit_kmh=row.speed_limit_kmh,
    )


def to_domain_assignment(row: PersistedAssignment) -> Assignment:
    return Assignment(
        assignment_id=row.assignment_id or str(uuid.uuid4()),
        driver_id=row.driver_id,
        vehicle_id=row.vehicle_id,
        route_id=row.route_id,
    )


def build_fleet_configuration(
    assignments: list[PersistedAssignment],
    drivers: dict[str, PersistedDriver],
    vehicles: dict[str, PersistedVehicle],
    routes: dict[str, PersistedRoute],
) -> FleetConfiguration:
    """Compose a :class:`FleetConfiguration` from persisted rows.

    ``assignments`` select which (driver, vehicle, route) triples take
    part in the scenario; lookups are provided as id-keyed dicts. Only
    active, resolvable assignments are included.
    """
    domain_vehicles: list[Vehicle] = []
    domain_drivers: list[Driver] = []
    domain_routes: list[Route] = []
    domain_assignments: list[Assignment] = []

    for row in assignments:
        if row.driver_id not in drivers:
            continue
        if row.vehicle_id not in vehicles:
            continue
        if row.route_id not in routes:
            continue

        driver = to_domain_driver(drivers[row.driver_id])
        vehicle = to_domain_vehicle(vehicles[row.vehicle_id])
        route = to_domain_route(routes[row.route_id])

        if vehicle.vehicle_id not in {v.vehicle_id for v in domain_vehicles}:
            domain_vehicles.append(vehicle)
        if driver.driver_id not in {d.driver_id for d in domain_drivers}:
            domain_drivers.append(driver)
        if route.route_id not in {r.route_id for r in domain_routes}:
            domain_routes.append(route)

        domain_assignments.append(to_domain_assignment(row))

    return FleetConfiguration(
        vehicles=domain_vehicles,
        drivers=domain_drivers,
        routes=domain_routes,
        assignments=domain_assignments,
    )
