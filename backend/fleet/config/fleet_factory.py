from dataclasses import dataclass

from backend.fleet.config.fleet_config import (
    ASSIGNMENTS,
    DRIVERS,
    ROUTES,
    VEHICLES,
)

from backend.fleet.models.assignment import Assignment
from backend.fleet.models.driver import Driver
from backend.fleet.models.route import Route
from backend.fleet.models.vehicle import Vehicle


@dataclass
class FleetConfiguration:
    vehicles: list[Vehicle]
    drivers: list[Driver]
    routes: list[Route]
    assignments: list[Assignment]


class FleetFactory:
    """
    Converts fleet configuration into runtime domain objects.

    Configuration:
        fleet_config.py

    Output:
        Vehicle
        Driver
        Route
        Assignment
    """

    @classmethod
    def from_config(cls) -> FleetConfiguration:
        vehicles = cls._create_vehicles()
        drivers = cls._create_drivers()
        routes = cls._create_routes()

        assignments = cls._create_assignments(
            vehicles=vehicles,
            drivers=drivers,
            routes=routes,
        )

        return FleetConfiguration(
            vehicles=vehicles,
            drivers=drivers,
            routes=routes,
            assignments=assignments,
        )

    @staticmethod
    def _create_vehicles() -> list[Vehicle]:
        return [
            Vehicle(
                vehicle_id=config["vehicle_id"],
                make=config["make"],
                model=config["model"],
                year=config["year"],
                odometer_km=config["odometer_km"],
                fuel_level_percent=config["fuel_level_percent"],
            )
            for config in VEHICLES
        ]

    @staticmethod
    def _create_drivers() -> list[Driver]:
        return [
            Driver(
                driver_id=config["driver_id"],
                name=config["name"],
                behavior_profile=config["behavior_profile"],
            )
            for config in DRIVERS
        ]

    @staticmethod
    def _create_routes() -> list[Route]:
        return [
            Route(
                route_id=config["route_id"],
                origin=config["origin"],
                destination=config["destination"],
                distance_km=config["distance_km"],
                route_type=config["route_type"],
            )
            for config in ROUTES
        ]

    @staticmethod
    def _create_assignments(
        vehicles: list[Vehicle],
        drivers: list[Driver],
        routes: list[Route],
    ) -> list[Assignment]:
        vehicles_by_id = {
            vehicle.vehicle_id: vehicle
            for vehicle in vehicles
        }

        drivers_by_id = {
            driver.driver_id: driver
            for driver in drivers
        }

        routes_by_id = {
            route.route_id: route
            for route in routes
        }

        assignments = []

        for config in ASSIGNMENTS:
            vehicle_id = config["vehicle_id"]
            driver_id = config["driver_id"]
            route_id = config["route_id"]

            if vehicle_id not in vehicles_by_id:
                raise ValueError(
                    f"Assignment references unknown vehicle: {vehicle_id}"
                )

            if driver_id not in drivers_by_id:
                raise ValueError(
                    f"Assignment references unknown driver: {driver_id}"
                )

            if route_id not in routes_by_id:
                raise ValueError(
                    f"Assignment references unknown route: {route_id}"
                )

            assignments.append(
                Assignment(
                   assignment_id=config["assignment_id"],
                   driver_id=driver_id,
                   vehicle_id=vehicle_id,
                   route_id=route_id,
                )
            )

        return assignments