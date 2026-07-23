"""
Assignment model.

Represents the operational relationship between a driver, a vehicle,
and a route: "which driver is assigned to which vehicle for which
route?" Intentionally minimal — no scheduling or fleet-management
logic lives here.
"""

from dataclasses import dataclass


@dataclass
class Assignment:
    assignment_id: str
    driver_id: str
    vehicle_id: str
    route_id: str