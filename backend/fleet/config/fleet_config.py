from backend.fleet.models.driver import BehaviorProfile


DRIVERS = [
    {
        "driver_id": "D-01",
        "name": "Driver 01",
        "behavior_profile": BehaviorProfile.AGGRESSIVE,
    },
    {
        "driver_id": "D-02",
        "name": "Driver 02",
        "behavior_profile": BehaviorProfile.ECO,
    },
    {
        "driver_id": "D-03",
        "name": "Driver 03",
        "behavior_profile": BehaviorProfile.CAUTIOUS,
    },
]


VEHICLES = [
    {
        "vehicle_id": "V-101",
        "make": "Ford",
        "model": "Transit",
        "year": 2023,
        "odometer_km": 14230.5,
        "fuel_level_percent": 87.0,
    },
    {
        "vehicle_id": "V-102",
        "make": "Mercedes",
        "model": "Sprinter",
        "year": 2024,
        "odometer_km": 8912.0,
        "fuel_level_percent": 95.0,
    },
    {
        "vehicle_id": "V-103",
        "make": "RAM",
        "model": "ProMaster",
        "year": 2022,
        "odometer_km": 52103.7,
        "fuel_level_percent": 62.0,
    },
]


ROUTES = [
    {
        "route_id": "R-01",
        "origin": "Warehouse",
        "destination": "Customer A",
        "distance_km": 5.0,
        "route_type": "urban",
    },
    {
        "route_id": "R-02",
        "origin": "Warehouse",
        "destination": "Customer B",
        "distance_km": 12.0,
        "route_type": "highway",
    },
    {
        "route_id": "R-03",
        "origin": "Warehouse",
        "destination": "Customer C",
        "distance_km": 3.5,
        "route_type": "urban",
    },
]


ASSIGNMENTS = [
    {
        "assignment_id": "A-101",
        "driver_id": "D-01",
        "vehicle_id": "V-101",
        "route_id": "R-01",
    },
    {
        "assignment_id": "A-102",
        "driver_id": "D-02",
        "vehicle_id": "V-102",
        "route_id": "R-02",
    },
]