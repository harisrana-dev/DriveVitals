"""Integration tests: persisted scenario assignments drive a real launch.

Covers the M4 contract end-to-end:
  * scenario creation persists ``scenario_assignments`` rows,
  * ``ScenarioRead`` serializes the persisted assignment ids,
  * launching the scenario wires the fleet that the assignments describe,
  * the run is recorded and stopped cleanly.

Uses real PostgreSQL rows and a live (fast-ticking) runtime, not mocked
ORM relationships.
"""

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from backend.api.v1.schemas.digital_twin import (
    AssignmentCreate,
    DriverCreate,
    RouteCreate,
    ScenarioCreate,
    ScenarioRead,
    VehicleCreate,
)
from backend.api.v1.services.digital_twin_service import DigitalTwinService
from backend.application.runtime import DriveVitalsRuntime
from backend.application.simulation_controller import SimulationController
from backend.db.models.assignment import Assignment
from backend.db.models.driver import Driver
from backend.db.models.route import Route
from backend.db.models.scenario import (
    SimulationRun,
    SimulationScenario,
    scenario_assignments,
)
from backend.db.models.vehicle import Vehicle
from backend.db.repositories import (
    AssignmentRepository,
    DriverRepository,
    RouteRepository,
    ScenarioRepository,
    VehicleRepository,
)
from backend.db.session import async_session_factory, close_db, init_db


async def _new_service(session, controller: SimulationController) -> DigitalTwinService:
    return DigitalTwinService(
        session,
        DriverRepository(session),
        VehicleRepository(session),
        RouteRepository(session),
        AssignmentRepository(session),
        ScenarioRepository(session),
        controller=controller,
    )


async def _seed_fleet(service: DigitalTwinService, prefix: str, count: int) -> list[str]:
    """Create ``count`` drivers/vehicles/routes and assignments; returns the
    persisted assignment ids."""
    ids = []
    for i in range(1, count + 1):
        driver_id = f"{prefix}-d{i}"
        vehicle_id = f"{prefix}-v{i}"
        route_id = f"{prefix}-r{i}"
        assignment_id = f"{prefix}-a{i}"
        await service.create_driver(
            DriverCreate(
                driver_id=driver_id,
                first_name=f"First{i}",
                last_name=f"Last{i}",
                license_number=f"{prefix}-LIC-{i}",
                behavior_profile="eco",
            )
        )
        await service.create_vehicle(
            VehicleCreate(
                vehicle_id=vehicle_id,
                registration_number=f"{prefix}-REG-{i}",
                vin=f"{prefix}VIN{i:05d}",
                manufacturer="Ford",
                model="Transit",
                year=2024,
                fuel_efficiency_factor=0.9,
                acceleration_response=1.3,
                tank_capacity_liters=70.0,
            )
        )
        await service.create_route(
            RouteCreate(
                route_id=route_id,
                name=f"Route {prefix} {i}",
                route_type="urban",
                origin="O",
                destination=f"D{i}",
                estimated_distance_km=5.0,
                speed_limit_kmh=60.0,
            )
        )
        await service.create_assignment(
            AssignmentCreate(
                assignment_id=assignment_id,
                driver_id=driver_id,
                vehicle_id=vehicle_id,
                route_id=route_id,
            )
        )
        ids.append(assignment_id)
    return ids


async def _purge() -> None:
    """Delete every persisted row created by the sc-* test prefixes."""
    async with async_session_factory() as session:
        assignment_ids = select(Assignment.assignment_id).where(
            (Assignment.assignment_id.like("sc-%")) |
            (Assignment.driver_id.like("sc-%")) |
            (Assignment.vehicle_id.like("sc-%")) |
            (Assignment.route_id.like("sc-%"))
        )
        await session.execute(
            scenario_assignments.delete().where(
                scenario_assignments.c.assignment_id.in_(assignment_ids)
            )
        )
        scenario_ids = select(SimulationScenario.scenario_id).where(
            SimulationScenario.name.like("sc-%")
        )
        await session.execute(
            scenario_assignments.delete().where(
                scenario_assignments.c.scenario_id.in_(scenario_ids)
            )
        )
        await session.execute(
            SimulationRun.__table__.delete().where(
                SimulationRun.scenario_id.in_(scenario_ids)
            )
        )
        await session.execute(
            SimulationScenario.__table__.delete().where(
                SimulationScenario.name.like("sc-%")
            )
        )
        await session.execute(
            Assignment.__table__.delete().where(
                (Assignment.assignment_id.like("sc-%")) |
                (Assignment.driver_id.like("sc-%")) |
                (Assignment.vehicle_id.like("sc-%")) |
                (Assignment.route_id.like("sc-%"))
            )
        )
        await session.execute(
            Driver.__table__.delete().where(Driver.driver_id.like("sc-%"))
        )
        await session.execute(
            Vehicle.__table__.delete().where(Vehicle.vehicle_id.like("sc-%"))
        )
        await session.execute(
            Route.__table__.delete().where(Route.route_id.like("sc-%"))
        )
        await session.commit()


async def test_scenario_assignments_flow_into_launch():
    await init_db()
    await _purge()
    runtime = DriveVitalsRuntime(tick_seconds=0.01)
    controller = SimulationController(runtime)
    try:
        async with async_session_factory() as session:
            service = await _new_service(session, controller)
            assignment_ids = await _seed_fleet(service, "sc-launch", 2)

            scenario = await service.create_scenario(
                ScenarioCreate(name="Lifecycle Scenario", seed=11),
                assignment_ids=assignment_ids,
            )
            scenario_id = scenario.scenario_id

            # scenario_assignments rows exist for exactly the given ids
            result = await session.execute(
                select(scenario_assignments.c.assignment_id).where(
                    scenario_assignments.c.scenario_id == scenario_id
                )
            )
            assert sorted(result.scalars().all()) == sorted(assignment_ids)

            # Serialization reflects the persisted relationship
            read = ScenarioRead.model_validate(scenario)
            assert sorted(read.assignment_ids) == sorted(assignment_ids)

            await service.activate_scenario(scenario_id)
            run, status = await service.launch_scenario(scenario_id)

            assert status["running"] is True
            assert run.scenario_id == scenario_id

            # The running fleet is built from the scenario's assignments.
            vehicle_ids = {r.vehicle.vehicle_id for r in runtime.fleet._runners}
            driver_names = {r.driver.name for r in runtime.fleet._runners}
            assert vehicle_ids == {"sc-launch-v1", "sc-launch-v2"}
            assert "First1 Last1" in driver_names
            assert "First2 Last2" in driver_names

            # Run recorded via the API surface
            runs, count = await service.list_runs(scenario_id, 100, 0)
            assert count == 1
            assert runs[0].run_id == run.run_id
            assert runs[0].status == "running"

            await controller.stop()
            assert controller.running is False
    finally:
        await controller.stop()
        await _purge()
        await close_db()


async def test_invalid_assignment_service_level_creates_no_scenario():
    await init_db()
    await _purge()
    runtime = DriveVitalsRuntime(tick_seconds=0.01)
    controller = SimulationController(runtime)
    try:
        async with async_session_factory() as session:
            service = await _new_service(session, controller)
            await _seed_fleet(service, "sc-inv", 1)

            with pytest.raises(HTTPException) as exc_info:
                await service.create_scenario(
                    ScenarioCreate(name="Should Not Exist"),
                    assignment_ids=["missing-assignment-99"],
                )
            assert exc_info.value.status_code == 404

        # Request session closed (rolled back) — nothing leaked to a fresh one.
        async with async_session_factory() as fresh:
            result = await fresh.execute(
                select(SimulationScenario).where(
                    SimulationScenario.name == "Should Not Exist"
                )
            )
            assert result.scalar_one_or_none() is None
    finally:
        await controller.stop()
        await _purge()
        await close_db()