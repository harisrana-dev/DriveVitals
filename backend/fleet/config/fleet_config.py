from backend.fleet.models.driver import BehaviorProfile


DRIVERS = [
    {
        "driver_id": "D-01",
        "name": "Ahmed Hassan",
        "behavior_profile": BehaviorProfile.CAUTIOUS,
    },
    {
        "driver_id": "D-02",
        "name": "Ali Imtiaz",
        "behavior_profile": BehaviorProfile.ECO,
    },
    {
        "driver_id": "D-03",
        "name": "Haris Kamal",
        "behavior_profile": BehaviorProfile.AGGRESSIVE,
    },
    {
        "driver_id": "D-04",
        "name": "Mian Salman",
        "behavior_profile": BehaviorProfile.AGGRESSIVE,
    },
    {
        "driver_id": "D-05",
        "name": "Wahad Ahmed",
        "behavior_profile": BehaviorProfile.ECO,
    },
    {
        "driver_id": "D-06",
        "name": "Sarah Azeez",
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
    {
        "vehicle_id": "V-104",
        "make": "Toyota",
        "model": "Tacoma",
        "year": 2023,
        "odometer_km": 18500.0,
        "fuel_level_percent": 73.0,
    },
    {
        "vehicle_id": "V-105",
        "make": "Nissan",
        "model": "Frontier",
        "year": 2024,
        "odometer_km": 9200.0,
        "fuel_level_percent": 91.0,
    },
    {
        "vehicle_id": "V-106",
        "make": "GMC",
        "model": "Sierra",
        "year": 2023,
        "odometer_km": 25400.0,
        "fuel_level_percent": 45.0,
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
    {
        "route_id": "R-04",
        "origin": "Depot",
        "destination": "Warehouse",
        "distance_km": 8.0,
        "route_type": "highway",
    },
    {
        "route_id": "R-05",
        "origin": "Warehouse",
        "destination": "Customer D",
        "distance_km": 6.5,
        "route_type": "urban",
    },
    {
        "route_id": "R-06",
        "origin": "Depot",
        "destination": "Customer E",
        "distance_km": 10.0,
        "route_type": "highway",
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
    {
        "assignment_id": "A-103",
        "driver_id": "D-03",
        "vehicle_id": "V-103",
        "route_id": "R-03",
    },
    {
        "assignment_id": "A-104",
        "driver_id": "D-04",
        "vehicle_id": "V-104",
        "route_id": "R-04",
    },
    {
        "assignment_id": "A-105",
        "driver_id": "D-05",
        "vehicle_id": "V-105",
        "route_id": "R-05",
    },
    {
        "assignment_id": "A-106",
        "driver_id": "D-06",
        "vehicle_id": "V-106",
        "route_id": "R-06",
    },
]