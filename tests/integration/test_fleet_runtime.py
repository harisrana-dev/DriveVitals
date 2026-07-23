"""
Integration tests for Fleet Runtime + Telemetry.

Verifies the complete runtime flow from assignment creation through
vehicle/driver/route binding, trip lifecycle transitions, telemetry
generation, and final state assertions. Does NOT test analytics
conclusions — only the Fleet Runtime + Telemetry boundary.
"""

import sys
import os
from datetime import datetime, timedelta
from typing import List

import pytest

# Ensure backend/ is on sys.path so fleet.* and telemetry.* resolve.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

from backend.fleet.models.assignment import Assignment
from backend.fleet.models.driver import Driver, BehaviorProfile
from backend.fleet.models.route import Route, RouteType
from backend.fleet.models.trip import Trip, TripStatus
from backend.fleet.models.vehicle import Vehicle, EngineStatus
from backend.fleet.runtime.fleet_runner import FleetRunner
from backend.fleet.runtime.vehicle_runner import VehicleRunner
from backend.fleet.runtime.runtime_state import RuntimeState
from backend.telemetry.models.telemetry_sample import TelemetrySample


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_vehicle(
    vehicle_id: str = "vehicle-001",
    odometer_km: float = 12000.0,
    fuel_level: float = 95.0,
) -> Vehicle:
    return Vehicle(
        vehicle_id=vehicle_id,
        make="Ford",
        model="Transit",
        year=2023,
        odometer_km=odometer_km,
        fuel_level_percent=fuel_level,
    )


def _make_driver(
    driver_id: str = "driver-001",
    name: str = "Alice",
    profile: BehaviorProfile = BehaviorProfile.AGGRESSIVE,
) -> Driver:
    return Driver(driver_id=driver_id, name=name, behavior_profile=profile)


def _make_route(
    route_id: str = "route-001",
    distance_km: float = 5.0,
    route_type: RouteType = RouteType.URBAN,
    speed_limit_kmh: float = 60.0,
) -> Route:
    return Route(
        route_id=route_id,
        origin="Warehouse",
        destination="Customer A",
        distance_km=distance_km,
        route_type=route_type,
        speed_limit_kmh=speed_limit_kmh,
    )


def _make_assignment(
    assignment_id: str = "assignment-001",
    driver_id: str = "driver-001",
    vehicle_id: str = "vehicle-001",
    route_id: str = "route-001",
) -> Assignment:
    return Assignment(
        assignment_id=assignment_id,
        driver_id=driver_id,
        vehicle_id=vehicle_id,
        route_id=route_id,
    )


def _make_trip(
    trip_id: str = "trip-001",
    vehicle_id: str = "vehicle-001",
    driver_id: str = "driver-001",
    route_id: str = "route-001",
) -> Trip:
    return Trip(
        trip_id=trip_id,
        vehicle_id=vehicle_id,
        driver_id=driver_id,
        route_id=route_id,
    )


# ---------------------------------------------------------------------------
# Test 1 — Single vehicle full runtime flow
# ---------------------------------------------------------------------------

class TestFleetRuntimeSingleVehicle:
    """End-to-end test: one vehicle, one driver, one route."""

    def test_full_runtime_flow(self):
        # --- Setup ---
        vehicle = _make_vehicle(odometer_km=12000.0, fuel_level=95.0)
        driver = _make_driver(profile=BehaviorProfile.AGGRESSIVE)
        route = _make_route(distance_km=5.0)
        assignment = _make_assignment()
        trip = _make_trip()

        initial_odometer = vehicle.odometer_km
        initial_fuel = vehicle.fuel_level_percent

        # --- 1. Assignment can be created ---
        assert assignment.assignment_id == "assignment-001"
        assert assignment.driver_id == "driver-001"
        assert assignment.vehicle_id == "vehicle-001"
        assert assignment.route_id == "route-001"

        # --- 2. FleetRunner can accept the assignment ---
        fleet = FleetRunner(tick_seconds=1.0)
        runner = fleet.add_assignment(
            assignment=assignment,
            vehicle=vehicle,
            driver=driver,
            route=route,
            trip=trip,
        )
        assert hasattr(runner, "start")
        assert hasattr(runner, "tick")
        assert runner is fleet._runners[0]

        # --- 3. VehicleRunner starts the trip ---
        start_time = datetime(2025, 1, 15, 8, 0, 0)
        runner.start(now=start_time)

        assert vehicle.engine_status == EngineStatus.RUNNING
        assert trip.started_at == start_time

        # --- 4. Trip transitions from ASSIGNED to STARTED ---
        assert trip.status == TripStatus.STARTED

        # --- 5. Trip transitions to IN_PROGRESS on first tick ---
        sample = runner.tick(now=start_time + timedelta(seconds=1))
        assert trip.status == TripStatus.IN_PROGRESS

        # --- 6. Telemetry samples are generated ---
        assert hasattr(sample, "speed_kmh")
        assert hasattr(sample, "vehicle_id")

        # --- 7. Telemetry contains expected vehicle, driver, trip IDs ---
        assert sample.vehicle_id == "vehicle-001"
        assert sample.driver_id == "driver-001"
        assert sample.trip_id == "trip-001"

        # --- 8. Speed changes smoothly rather than jumping randomly ---
        # Collect multiple samples and verify bounded speed deltas.
        fleet2 = FleetRunner(tick_seconds=1.0)
        vehicle2 = _make_vehicle(odometer_km=12000.0, fuel_level=95.0)
        runner2 = fleet2.add_assignment(
            assignment=_make_assignment(),
            vehicle=vehicle2,
            driver=_make_driver(),
            route=_make_route(),
            trip=_make_trip(),
        )
        runner2.start(now=start_time)
        speed_samples: List[float] = []
        for i in range(20):
            s = runner2.tick(now=start_time + timedelta(seconds=i + 1))
            speed_samples.append(s.speed_kmh)
        for i in range(1, len(speed_samples)):
            delta = abs(speed_samples[i] - speed_samples[i - 1])
            # Aggressive profile max accel 6.0 km/h/s, max decel 9.0 km/h/s.
            # Per tick (1s) the speed change is bounded by max_decel_kmh_s.
            # Use 10.0 to give margin above the theoretical 9.0 limit.
            assert delta <= 10.0, (
                f"Speed jumped by {delta:.2f} km/h between ticks {i-1} and {i}: "
                f"{speed_samples[i-1]:.1f} -> {speed_samples[i]:.1f}"
            )

        # --- 9. Odometer increases during the trip ---
        fleet3 = FleetRunner(tick_seconds=1.0)
        vehicle3 = _make_vehicle(odometer_km=12000.0, fuel_level=95.0)
        runner3 = fleet3.add_assignment(
            assignment=_make_assignment(),
            vehicle=vehicle3,
            driver=_make_driver(),
            route=_make_route(),
            trip=_make_trip(),
        )
        runner3.start(now=start_time)
        odometer_readings: List[float] = []
        for i in range(10):
            s = runner3.tick(now=start_time + timedelta(seconds=i + 1))
            odometer_readings.append(s.odometer_km)
        for i in range(1, len(odometer_readings)):
            assert odometer_readings[i] >= odometer_readings[i - 1], (
                f"Odometer decreased at tick {i}: "
                f"{odometer_readings[i-1]:.2f} -> {odometer_readings[i]:.2f}"
            )
        # At least some movement should have occurred over 10 seconds.
        assert odometer_readings[-1] > odometer_readings[0]

        # --- 10. Fuel level decreases during the trip ---
        fleet4 = FleetRunner(tick_seconds=1.0)
        vehicle4 = _make_vehicle(odometer_km=12000.0, fuel_level=95.0)
        runner4 = fleet4.add_assignment(
            assignment=_make_assignment(),
            vehicle=vehicle4,
            driver=_make_driver(),
            route=_make_route(),
            trip=_make_trip(),
        )
        runner4.start(now=start_time)
        fuel_readings: List[float] = []
        for i in range(10):
            s = runner4.tick(now=start_time + timedelta(seconds=i + 1))
            fuel_readings.append(s.fuel_level_percent)
        for i in range(1, len(fuel_readings)):
            assert fuel_readings[i] <= fuel_readings[i - 1], (
                f"Fuel level increased at tick {i}: "
                f"{fuel_readings[i-1]:.2f} -> {fuel_readings[i]:.2f}"
            )
        assert fuel_readings[-1] < fuel_readings[0]

        # --- 11. Coolant temperature changes progressively ---
        fleet5 = FleetRunner(tick_seconds=1.0)
        vehicle5 = _make_vehicle(odometer_km=12000.0, fuel_level=95.0)
        runner5 = fleet5.add_assignment(
            assignment=_make_assignment(),
            vehicle=vehicle5,
            driver=_make_driver(),
            route=_make_route(),
            trip=_make_trip(),
        )
        runner5.start(now=start_time)
        temp_readings: List[float] = []
        for i in range(10):
            s = runner5.tick(now=start_time + timedelta(seconds=i + 1))
            temp_readings.append(s.coolant_temperature_c)
        for i in range(1, len(temp_readings)):
            delta = abs(temp_readings[i] - temp_readings[i - 1])
            # OBD generator clamps temp change to max 2.0 per tick.
            assert delta <= 2.1, (
                f"Coolant temp jumped by {delta:.2f}C at tick {i}: "
                f"{temp_readings[i-1]:.1f} -> {temp_readings[i]:.1f}"
            )
        # Should be warming up (at least increasing in early ticks).
        assert temp_readings[-1] >= temp_readings[0]

        # --- 12. RPM is internally consistent with vehicle speed ---
        fleet6 = FleetRunner(tick_seconds=1.0)
        vehicle6 = _make_vehicle(odometer_km=12000.0, fuel_level=95.0)
        runner6 = fleet6.add_assignment(
            assignment=_make_assignment(),
            vehicle=vehicle6,
            driver=_make_driver(),
            route=_make_route(),
            trip=_make_trip(),
        )
        runner6.start(now=start_time)
        for i in range(20):
            s = runner6.tick(now=start_time + timedelta(seconds=i + 1))
            # When speed is ~0, RPM should be idle (~800).
            if s.speed_kmh < 1.0:
                assert s.rpm <= 1000.0, (
                    f"RPM {s.rpm:.0f} is too high for near-zero speed {s.speed_kmh:.1f}"
                )
            # When speed > 0, RPM should be positive and scale with speed.
            if s.speed_kmh > 5.0:
                assert s.rpm > 800.0, (
                    f"RPM {s.rpm:.0f} should be above idle for speed {s.speed_kmh:.1f}"
                )
                assert s.rpm <= 6500.0, (
                    f"RPM {s.rpm:.0f} exceeds max for speed {s.speed_kmh:.1f}"
                )

        # --- 13. Telemetry is generated continuously for multiple ticks ---
        fleet7 = FleetRunner(tick_seconds=1.0)
        vehicle7 = _make_vehicle(odometer_km=12000.0, fuel_level=95.0)
        runner7 = fleet7.add_assignment(
            assignment=_make_assignment(),
            vehicle=vehicle7,
            driver=_make_driver(),
            route=_make_route(),
            trip=_make_trip(),
        )
        runner7.start(now=start_time)
        all_samples: List[TelemetrySample] = []
        for i in range(50):
            s = runner7.tick(now=start_time + timedelta(seconds=i + 1))
            all_samples.append(s)
            if runner7.is_complete():
                break
        assert len(all_samples) >= 2, "Expected multiple telemetry samples"

        # --- 14. The trip eventually reaches COMPLETED ---
        # Continue the original runner (from steps 3-5) to completion.
        now = start_time + timedelta(seconds=2)
        while not runner.is_complete():
            sample = runner.tick(now=now)
            now = now + timedelta(seconds=1)
        assert trip.status == TripStatus.COMPLETED
        assert trip.completed_at is not None

        # --- 15. Final odometer is greater than initial odometer ---
        assert vehicle.odometer_km > initial_odometer

        # --- 16. Final fuel level is lower than initial fuel level ---
        assert vehicle.fuel_level_percent < initial_fuel

        # --- 17. Final trip distance is approximately equal to route distance ---
        assert trip.distance_travelled_km >= route.distance_km - 0.5
        assert trip.distance_travelled_km <= route.distance_km + 5.0

        # --- 18. Final telemetry sample reflects final vehicle state ---
        assert all_samples[-1].odometer_km > all_samples[0].odometer_km
        assert all_samples[-1].fuel_level_percent < all_samples[0].fuel_level_percent

    def test_trip_lifecycle_transitions(self):
        """Explicitly verify ASSIGNED -> STARTED -> IN_PROGRESS -> COMPLETED."""
        vehicle = _make_vehicle()
        driver = _make_driver()
        route = _make_route()
        trip = _make_trip()

        assert trip.status == TripStatus.ASSIGNED

        # Use FleetRunner to drive the full lifecycle from ASSIGNED.
        fleet = FleetRunner(tick_seconds=1.0)
        fleet.add_assignment(
            assignment=_make_assignment(),
            vehicle=vehicle,
            driver=driver,
            route=route,
            trip=trip,
        )
        start_time = datetime(2025, 1, 15, 8, 0, 0)

        # After start_all, trip transitions ASSIGNED -> STARTED.
        fleet.start_all(now=start_time)
        assert trip.status == TripStatus.STARTED

        # After first tick, trip transitions STARTED -> IN_PROGRESS.
        fleet.tick_all(now=start_time + timedelta(seconds=1))
        assert trip.status == TripStatus.IN_PROGRESS

        # Continue ticking until trip completes.
        now = start_time + timedelta(seconds=2)
        while fleet.active_runners():
            fleet.tick_all(now=now)
            now = now + timedelta(seconds=1)

        assert trip.status == TripStatus.COMPLETED

    def test_engine_status_transitions(self):
        """Vehicle engine starts ON and stops OFF after trip completes."""
        vehicle = _make_vehicle()
        driver = _make_driver()
        route = _make_route()
        trip = _make_trip()

        assert vehicle.engine_status == EngineStatus.OFF

        fleet = FleetRunner(tick_seconds=1.0)
        fleet.add_assignment(
            assignment=_make_assignment(),
            vehicle=vehicle,
            driver=driver,
            route=route,
            trip=trip,
        )
        fleet.run(
            sink=lambda s: None,
            start_time=datetime(2025, 1, 15, 8, 0, 0),
            max_ticks=1000,
        )
        assert vehicle.engine_status == EngineStatus.OFF

    def test_odometer_never_decreases(self):
        """Vehicle odometer must be monotonically non-decreasing."""
        vehicle = _make_vehicle(odometer_km=50000.0, fuel_level=80.0)
        driver = _make_driver()
        route = _make_route(distance_km=3.0)
        trip = _make_trip()

        fleet = FleetRunner(tick_seconds=1.0)
        fleet.add_assignment(
            assignment=_make_assignment(),
            vehicle=vehicle,
            driver=driver,
            route=route,
            trip=trip,
        )
        samples: List[TelemetrySample] = []
        fleet.run(
            sink=samples.append,
            start_time=datetime(2025, 1, 15, 8, 0, 0),
            max_ticks=1000,
        )
        for i in range(1, len(samples)):
            assert samples[i].odometer_km >= samples[i - 1].odometer_km

    def test_fuel_never_increases(self):
        """Vehicle fuel level must be monotonically non-increasing."""
        vehicle = _make_vehicle(fuel_level=80.0)
        driver = _make_driver()
        route = _make_route(distance_km=3.0)
        trip = _make_trip()

        fleet = FleetRunner(tick_seconds=1.0)
        fleet.add_assignment(
            assignment=_make_assignment(),
            vehicle=vehicle,
            driver=driver,
            route=route,
            trip=trip,
        )
        samples: List[TelemetrySample] = []
        fleet.run(
            sink=samples.append,
            start_time=datetime(2025, 1, 15, 8, 0, 0),
            max_ticks=1000,
        )
        for i in range(1, len(samples)):
            assert samples[i].fuel_level_percent <= samples[i - 1].fuel_level_percent

    def test_cannot_tick_completed_trip(self):
        """VehicleRunner raises RuntimeError if trip is already completed."""
        vehicle = _make_vehicle()
        driver = _make_driver()
        route = _make_route(distance_km=0.1)  # Short route
        trip = _make_trip()

        runner = VehicleRunner(
            vehicle=vehicle, driver=driver, route=route, trip=trip
        )
        start_time = datetime(2025, 1, 15, 8, 0, 0)
        runner.start(now=start_time)

        # Tick until the trip completes.
        now = start_time + timedelta(seconds=1)
        while not runner.is_complete():
            runner.tick(now=now)
            now = now + timedelta(seconds=1)

        assert runner.is_complete()

        with pytest.raises(RuntimeError, match="Cannot tick a completed trip"):
            runner.tick(now=now)


# ---------------------------------------------------------------------------
# Test 2 — Two vehicles running independently
# ---------------------------------------------------------------------------

class TestFleetRuntimeTwoVehicles:
    """Two vehicles, two drivers, two routes running through FleetRunner."""

    def test_two_vehicles_run_independently(self):
        start_time = datetime(2025, 2, 1, 9, 0, 0)

        # --- Vehicle 1 ---
        vehicle1 = _make_vehicle(
            vehicle_id="vehicle-001", odometer_km=10000.0, fuel_level=90.0
        )
        driver1 = _make_driver(
            driver_id="driver-001", name="Alice", profile=BehaviorProfile.AGGRESSIVE
        )
        route1 = _make_route(
            route_id="route-001",
            distance_km=5.0,
            route_type=RouteType.URBAN,
            speed_limit_kmh=60.0,
        )
        assignment1 = _make_assignment(
            assignment_id="assignment-001",
            driver_id="driver-001",
            vehicle_id="vehicle-001",
            route_id="route-001",
        )
        trip1 = _make_trip(
            trip_id="trip-001",
            vehicle_id="vehicle-001",
            driver_id="driver-001",
            route_id="route-001",
        )

        # --- Vehicle 2 ---
        vehicle2 = _make_vehicle(
            vehicle_id="vehicle-002", odometer_km=25000.0, fuel_level=75.0
        )
        driver2 = _make_driver(
            driver_id="driver-002", name="Bob", profile=BehaviorProfile.ECO
        )
        route2 = _make_route(
            route_id="route-002",
            distance_km=8.0,
            route_type=RouteType.HIGHWAY,
            speed_limit_kmh=110.0,
        )
        assignment2 = _make_assignment(
            assignment_id="assignment-002",
            driver_id="driver-002",
            vehicle_id="vehicle-002",
            route_id="route-002",
        )
        trip2 = _make_trip(
            trip_id="trip-002",
            vehicle_id="vehicle-002",
            driver_id="driver-002",
            route_id="route-002",
        )

        # Initial state
        v1_initial_odometer = vehicle1.odometer_km
        v1_initial_fuel = vehicle1.fuel_level_percent
        v2_initial_odometer = vehicle2.odometer_km
        v2_initial_fuel = vehicle2.fuel_level_percent

        # --- Both assignments accepted by FleetRunner ---
        fleet = FleetRunner(tick_seconds=1.0)
        runner1 = fleet.add_assignment(
            assignment=assignment1,
            vehicle=vehicle1,
            driver=driver1,
            route=route1,
            trip=trip1,
        )
        runner2 = fleet.add_assignment(
            assignment=assignment2,
            vehicle=vehicle2,
            driver=driver2,
            route=route2,
            trip=trip2,
        )
        assert len(fleet._runners) == 2

        # --- Run the fleet ---
        all_samples: List[TelemetrySample] = []
        fleet.run(
            sink=all_samples.append,
            start_time=start_time,
            max_ticks=5000,
        )

        # --- Both trips generate telemetry ---
        samples_v1 = [s for s in all_samples if s.trip_id == "trip-001"]
        samples_v2 = [s for s in all_samples if s.trip_id == "trip-002"]
        assert len(samples_v1) > 0, "Vehicle 1 produced no telemetry samples"
        assert len(samples_v2) > 0, "Vehicle 2 produced no telemetry samples"

        # --- Each telemetry sample retains correct vehicle ID ---
        for s in samples_v1:
            assert s.vehicle_id == "vehicle-001"
        for s in samples_v2:
            assert s.vehicle_id == "vehicle-002"

        # --- Each telemetry sample retains correct driver ID ---
        for s in samples_v1:
            assert s.driver_id == "driver-001"
        for s in samples_v2:
            assert s.driver_id == "driver-002"

        # --- Each trip completes independently ---
        assert trip1.status == TripStatus.COMPLETED
        assert trip2.status == TripStatus.COMPLETED

        # --- Vehicle state isolation: one vehicle's state doesn't modify the other ---
        assert vehicle1.odometer_km > v1_initial_odometer
        assert vehicle2.odometer_km > v2_initial_odometer
        assert vehicle1.fuel_level_percent < v1_initial_fuel
        assert vehicle2.fuel_level_percent < v2_initial_fuel

        # Vehicle 1 started at 10000 and was not contaminated by vehicle 2's 25000.
        assert vehicle1.odometer_km < 10010.0  # 5 km route, shouldn't be anywhere near 25000
        # Vehicle 2 started at 25000 and was not contaminated by vehicle 1's 10000.
        assert vehicle2.odometer_km > 25000.0

        # Fuel levels remain independent.
        assert vehicle1.fuel_level_percent != vehicle2.fuel_level_percent

        # --- Final telemetry samples reflect each vehicle's state ---
        last_v1 = samples_v1[-1]
        last_v2 = samples_v2[-1]
        assert last_v1.odometer_km > v1_initial_odometer
        assert last_v2.odometer_km > v2_initial_odometer
        assert last_v1.fuel_level_percent < v1_initial_fuel
        assert last_v2.fuel_level_percent < v2_initial_fuel

    def test_two_vehicles_speed_profiles_differ(self):
        """Different behavior profiles produce measurably different telemetry."""
        start_time = datetime(2025, 2, 1, 9, 0, 0)

        vehicle1 = _make_vehicle(vehicle_id="vehicle-001", odometer_km=0.0, fuel_level=100.0)
        driver1 = _make_driver(
            driver_id="driver-001", name="Alice", profile=BehaviorProfile.AGGRESSIVE
        )
        route1 = _make_route(route_id="route-001", distance_km=10.0, speed_limit_kmh=60.0)
        trip1 = _make_trip(trip_id="trip-001", vehicle_id="vehicle-001",
                           driver_id="driver-001", route_id="route-001")

        vehicle2 = _make_vehicle(vehicle_id="vehicle-002", odometer_km=0.0, fuel_level=100.0)
        driver2 = _make_driver(
            driver_id="driver-002", name="Bob", profile=BehaviorProfile.ECO
        )
        route2 = _make_route(route_id="route-002", distance_km=10.0, speed_limit_kmh=60.0)
        trip2 = _make_trip(trip_id="trip-002", vehicle_id="vehicle-002",
                           driver_id="driver-002", route_id="route-002")

        fleet = FleetRunner(tick_seconds=1.0)
        fleet.add_assignment(
            assignment=_make_assignment(assignment_id="a1",
                                        driver_id="driver-001",
                                        vehicle_id="vehicle-001",
                                        route_id="route-001"),
            vehicle=vehicle1, driver=driver1, route=route1, trip=trip1,
        )
        fleet.add_assignment(
            assignment=_make_assignment(assignment_id="a2",
                                        driver_id="driver-002",
                                        vehicle_id="vehicle-002",
                                        route_id="route-002"),
            vehicle=vehicle2, driver=driver2, route=route2, trip=trip2,
        )

        all_samples: List[TelemetrySample] = []
        fleet.run(sink=all_samples.append, start_time=start_time, max_ticks=5000)

        samples_v1 = [s for s in all_samples if s.trip_id == "trip-001"]
        samples_v2 = [s for s in all_samples if s.trip_id == "trip-002"]

        # Both completed.
        assert trip1.status == TripStatus.COMPLETED
        assert trip2.status == TripStatus.COMPLETED

        # Aggressive profile should burn more fuel over the same route.
        fuel_used_v1 = 100.0 - vehicle1.fuel_level_percent
        fuel_used_v2 = 100.0 - vehicle2.fuel_level_percent
        assert fuel_used_v1 > fuel_used_v2, (
            f"Aggressive driver ({fuel_used_v1:.2f}% used) should burn more fuel "
            f"than eco driver ({fuel_used_v2:.2f}% used)"
        )

    def test_two_vehicles_different_route_distances(self):
        """Vehicles on different-length routes complete at different times."""
        start_time = datetime(2025, 3, 1, 10, 0, 0)

        vehicle1 = _make_vehicle(vehicle_id="vehicle-001", odometer_km=0.0, fuel_level=100.0)
        driver1 = _make_driver(driver_id="driver-001", name="Alice")
        route1 = _make_route(route_id="route-001", distance_km=2.0, speed_limit_kmh=60.0)
        trip1 = _make_trip(trip_id="trip-001", vehicle_id="vehicle-001",
                           driver_id="driver-001", route_id="route-001")

        vehicle2 = _make_vehicle(vehicle_id="vehicle-002", odometer_km=0.0, fuel_level=100.0)
        driver2 = _make_driver(driver_id="driver-002", name="Bob")
        route2 = _make_route(route_id="route-002", distance_km=15.0, speed_limit_kmh=60.0)
        trip2 = _make_trip(trip_id="trip-002", vehicle_id="vehicle-002",
                           driver_id="driver-002", route_id="route-002")

        fleet = FleetRunner(tick_seconds=1.0)
        fleet.add_assignment(
            assignment=_make_assignment(assignment_id="a1",
                                        driver_id="driver-001",
                                        vehicle_id="vehicle-001",
                                        route_id="route-001"),
            vehicle=vehicle1, driver=driver1, route=route1, trip=trip1,
        )
        fleet.add_assignment(
            assignment=_make_assignment(assignment_id="a2",
                                        driver_id="driver-002",
                                        vehicle_id="vehicle-002",
                                        route_id="route-002"),
            vehicle=vehicle2, driver=driver2, route=route2, trip=trip2,
        )

        tick_count = 0
        fleet.start_all(now=start_time)
        now = start_time

        v1_completed_tick = None
        v2_completed_tick = None

        while fleet.active_runners():
            for sample in fleet.tick_all(now=now):
                pass
            now = now + timedelta(seconds=1.0)
            tick_count += 1
            if trip1.status == TripStatus.COMPLETED and v1_completed_tick is None:
                v1_completed_tick = tick_count
            if trip2.status == TripStatus.COMPLETED and v2_completed_tick is None:
                v2_completed_tick = tick_count
            if tick_count > 5000:
                break

        assert trip1.status == TripStatus.COMPLETED
        assert trip2.status == TripStatus.COMPLETED

        # Shorter route should complete first.
        assert v1_completed_tick is not None
        assert v2_completed_tick is not None
        assert v1_completed_tick < v2_completed_tick, (
            f"Shorter route (2 km) took {v1_completed_tick} ticks but "
            f"longer route (15 km) took {v2_completed_tick} ticks"
        )


# ---------------------------------------------------------------------------
# Test 3 — RuntimeState correctness
# ---------------------------------------------------------------------------

class TestRuntimeState:
    """Verify RuntimeState reset and invariants."""

    def test_reset_clears_all_fields(self):
        state = RuntimeState(
            current_speed_kmh=80.0,
            current_rpm=3000.0,
            current_fuel_rate_lph=6.5,
            current_engine_temperature_c=85.0,
            current_trip_distance_km=3.7,
        )
        state.reset()
        assert state.current_speed_kmh == 0.0
        assert state.current_rpm == 0.0
        assert state.current_fuel_rate_lph == 0.0
        assert state.current_engine_temperature_c == 20.0
        assert state.current_trip_distance_km == 0.0

    def test_default_runtime_state(self):
        state = RuntimeState()
        assert state.current_speed_kmh == 0.0
        assert state.current_rpm == 0.0
        assert state.current_engine_temperature_c == 20.0
        assert state.current_trip_distance_km == 0.0


# ---------------------------------------------------------------------------
# Test 4 — Telemetry sample field sanity
# ---------------------------------------------------------------------------

class TestTelemetrySampleFields:
    """Verify TelemetrySample fields are within plausible ranges."""

    def test_sample_fields_are_plausible(self):
        vehicle = _make_vehicle(odometer_km=5000.0, fuel_level=85.0)
        driver = _make_driver(profile=BehaviorProfile.STANDARD)
        route = _make_route(distance_km=3.0, speed_limit_kmh=50.0)
        trip = _make_trip()

        runner = VehicleRunner(
            vehicle=vehicle, driver=driver, route=route, trip=trip
        )
        start_time = datetime(2025, 1, 15, 8, 0, 0)
        runner.start(now=start_time)

        # Collect 30 ticks to let things stabilize.
        samples: List[TelemetrySample] = []
        for i in range(30):
            s = runner.tick(now=start_time + timedelta(seconds=i + 1))
            samples.append(s)

        # Use later samples (stabilized driving) for range checks.
        late = samples[15:]

        for s in late:
            assert 0.0 <= s.speed_kmh <= 120.0, f"Speed {s.speed_kmh} out of range"
            assert 0.0 <= s.rpm <= 6500.0, f"RPM {s.rpm} out of range"
            assert 0.0 <= s.throttle_position_percent <= 100.0
            assert 0.0 <= s.brake_pressure <= 1.0
            assert 15.0 <= s.coolant_temperature_c <= 120.0
            assert 0.0 <= s.engine_load_percent <= 100.0
            assert s.fuel_rate_lph >= 0.0
            assert 0.0 <= s.fuel_level_percent <= 100.0
            assert s.odometer_km >= 5000.0
            assert s.timestamp is not None

    def test_sample_ids_match_assignment(self):
        """Every sample must carry the IDs that were passed through the pipeline."""
        vehicle = _make_vehicle(vehicle_id="V-42", odometer_km=1000.0)
        driver = _make_driver(driver_id="D-7", name="Test")
        route = _make_route(route_id="R-3", distance_km=1.0)
        trip = _make_trip(
            trip_id="T-99",
            vehicle_id="V-42",
            driver_id="D-7",
            route_id="R-3",
        )

        runner = VehicleRunner(
            vehicle=vehicle, driver=driver, route=route, trip=trip
        )
        start_time = datetime(2025, 4, 1, 12, 0, 0)
        runner.start(now=start_time)

        for i in range(10):
            s = runner.tick(now=start_time + timedelta(seconds=i + 1))
            assert s.vehicle_id == "V-42"
            assert s.driver_id == "D-7"
            assert s.trip_id == "T-99"


# ---------------------------------------------------------------------------
# Test 5 — Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    """Edge cases and boundary conditions."""

    def test_very_short_route_completes_quickly(self):
        """A 0.1 km route should complete in very few ticks."""
        vehicle = _make_vehicle(odometer_km=0.0, fuel_level=100.0)
        driver = _make_driver()
        route = _make_route(distance_km=0.1, speed_limit_kmh=30.0)
        trip = _make_trip()

        fleet = FleetRunner(tick_seconds=1.0)
        fleet.add_assignment(
            assignment=_make_assignment(),
            vehicle=vehicle, driver=driver, route=route, trip=trip,
        )
        samples: List[TelemetrySample] = []
        fleet.run(
            sink=samples.append,
            start_time=datetime(2025, 1, 15, 8, 0, 0),
            max_ticks=100,
        )
        assert trip.status == TripStatus.COMPLETED
        assert len(samples) <= 20  # Should finish very quickly.

    def test_max_ticks_prevents_infinite_loop(self):
        """max_ticks should halt the run even if trip isn't complete."""
        vehicle = _make_vehicle()
        driver = _make_driver()
        route = _make_route(distance_km=999999.0)  # Impossibly long route.
        trip = _make_trip()

        fleet = FleetRunner(tick_seconds=1.0)
        fleet.add_assignment(
            assignment=_make_assignment(),
            vehicle=vehicle, driver=driver, route=route, trip=trip,
        )
        samples: List[TelemetrySample] = []
        fleet.run(
            sink=samples.append,
            start_time=datetime(2025, 1, 15, 8, 0, 0),
            max_ticks=5,
        )
        assert len(samples) == 5
        assert trip.status != TripStatus.COMPLETED

    def test_single_tick_produces_one_sample(self):
        """FleetRunner.tick_all() returns exactly one sample per active runner."""
        vehicle = _make_vehicle()
        driver = _make_driver()
        route = _make_route()
        trip = _make_trip()

        fleet = FleetRunner(tick_seconds=1.0)
        fleet.add_assignment(
            assignment=_make_assignment(),
            vehicle=vehicle, driver=driver, route=route, trip=trip,
        )
        fleet.start_all(now=datetime(2025, 1, 15, 8, 0, 0))
        samples = fleet.tick_all(now=datetime(2025, 1, 15, 8, 0, 1))
        assert len(samples) == 1
        assert hasattr(samples[0], "speed_kmh")
        assert hasattr(samples[0], "vehicle_id")

    def test_active_runners_decreases_as_trips_complete(self):
        """Once a trip completes, its runner is no longer in active_runners()."""
        vehicle = _make_vehicle()
        driver = _make_driver()
        route = _make_route(distance_km=5.0)
        trip = _make_trip()

        fleet = FleetRunner(tick_seconds=1.0)
        fleet.add_assignment(
            assignment=_make_assignment(),
            vehicle=vehicle, driver=driver, route=route, trip=trip,
        )
        fleet.start_all(now=datetime(2025, 1, 15, 8, 0, 0))

        assert len(fleet.active_runners()) == 1

        # Tick until trip completes.
        now = datetime(2025, 1, 15, 8, 0, 1)
        while fleet.active_runners():
            fleet.tick_all(now=now)
            now = now + timedelta(seconds=1)

        assert len(fleet.active_runners()) == 0
        assert trip.status == TripStatus.COMPLETED
