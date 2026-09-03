"""Integration tests for the Digital Twin simulation controller.

Exercises the live-runtime integration: configuring the fleet from a
scenario, launching/stopping/resetting the runtime task, and the
configure/reset fleet lifecycle. The runtime is created without a
persistence service so no database writes occur.
"""

import asyncio

import pytest

from backend.application.runtime import DriveVitalsRuntime
from backend.application.simulation_controller import SimulationController
from backend.fleet.config.fleet_factory import FleetConfiguration
from backend.fleet.models.assignment import Assignment
from backend.fleet.models.driver import Driver
from backend.fleet.models.route import Route
from backend.fleet.models.vehicle import Vehicle


def _build_config(vehicle_id="cv-1") -> FleetConfiguration:
    vehicle = Vehicle(
        vehicle_id=vehicle_id,
        make="Ford",
        model="Transit",
        year=2024,
        fuel_efficiency_factor=0.9,
        acceleration_response=1.3,
        tank_capacity_liters=70.0,
    )
    driver = Driver(driver_id="cd-1", name="Test Driver", behavior_profile="eco")
    route = Route(
        route_id="cr-1", origin="A", destination="B", distance_km=1.0,
        route_type="urban", speed_limit_kmh=50.0,
    )
    assignment = Assignment(
        assignment_id="ca-1", driver_id="cd-1", vehicle_id=vehicle_id, route_id="cr-1"
    )
    return FleetConfiguration(
        vehicles=[vehicle], drivers=[driver], routes=[route], assignments=[assignment]
    )


def _runtime() -> DriveVitalsRuntime:
    return DriveVitalsRuntime(tick_seconds=0.01)


async def test_launch_reconfigures_fleet():
    runtime = _runtime()
    controller = SimulationController(runtime)

    assert runtime.fleet._runners == [] or runtime.fleet._runners

    status = await controller.launch(
        _build_config(),
        scenario_id="s1",
        scenario_name="S1",
        run_id="r1",
        seed=7,
    )
    assert status["running"] is True
    assert status["scenario_id"] == "s1"
    assert status["vehicles"] == 1

    # The fleet now reflects the scenario's single vehicle.
    assert len(runtime.fleet._runners) == 1
    assert runtime.fleet._runners[0].vehicle.vehicle_id == "cv-1"

    # Let the task progress, then stop.
    await asyncio.sleep(0.05)
    status = await controller.stop()
    assert status["running"] is False
    assert status["scenario_id"] is None


async def test_launch_uses_vehicle_characteristics():
    runtime = _runtime()
    controller = SimulationController(runtime)
    await controller.launch(
        _build_config(),
        scenario_id="s2",
        scenario_name="S2",
        run_id="r2",
        seed=42,
    )
    vehicle = runtime.fleet._runners[0].vehicle
    assert vehicle.fuel_efficiency_factor == 0.9
    assert vehicle.acceleration_response == 1.3
    assert vehicle.tank_capacity_liters == 70.0
    await controller.stop()


async def test_reset_restores_default_fleet():
    runtime = _runtime()
    controller = SimulationController(runtime)
    await controller.launch(
        _build_config(),
        scenario_id="s3",
        scenario_name="S3",
        run_id="r3",
        seed=1,
    )
    assert len(runtime.fleet._runners) == 1

    await controller.reset()
    assert controller.running is False
    # Default factory fleet has 6 assignments.
    assert len(runtime.fleet._runners) == 6


async def test_running_reflects_task_lifecycle():
    runtime = _runtime()
    controller = SimulationController(runtime)
    assert controller.running is False
    await controller.launch(
        _build_config(),
        scenario_id="s4",
        scenario_name="S4",
        run_id="r4",
        seed=99,
    )
    assert controller.running is True
    await controller.stop()
    assert controller.running is False


async def test_launch_replaces_active_run():
    runtime = _runtime()
    controller = SimulationController(runtime)
    await controller.launch(
        _build_config("cv-1"),
        scenario_id="s5",
        scenario_name="S5",
        run_id="r5",
        seed=1,
    )
    await controller.launch(
        _build_config("cv-2"),
        scenario_id="s6",
        scenario_name="S6",
        run_id="r6",
        seed=2,
    )
    assert controller.scenario_id == "s6"
    assert runtime.fleet._runners[0].vehicle.vehicle_id == "cv-2"
    await controller.stop()
