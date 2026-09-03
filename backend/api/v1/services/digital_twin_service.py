"""Digital Twin Lab service.

Admin-only orchestration for managing the fleet (drivers, vehicles,
routes), assignments, simulation scenarios and their runs, and for
launching/stopping/resetting scenario simulations through the live
:class:`SimulationController`.

Domain rules enforced here:
* Assignments must reference existing drivers, vehicles and routes, and
  the (driver, vehicle, route) triple must be unique.
* Only a ``ready`` scenario may be launched.
* Launching/stopping requires the simulation controller to be available
  (i.e. the application runtime is wired up).
"""

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.api.simulation_state import SimulationController
from backend.api.v1.schemas import digital_twin as schemas
from backend.application.simulation_builder import build_fleet_configuration
from backend.db.models.assignment import Assignment as PersistedAssignment
from backend.db.models.driver import Driver as PersistedDriver
from backend.db.models.route import Route as PersistedRoute
from backend.db.models.scenario import SimulationRun, SimulationScenario
from backend.db.models.vehicle import Vehicle as PersistedVehicle

logger = logging.getLogger(__name__)

VALID_SCENARIO_STATUSES = {"draft", "ready", "running", "completed", "failed"}
VALID_RUN_STATUSES = {"ready", "running", "completed", "failed", "stopped"}


class DigitalTwinService:
    def __init__(
        self,
        session: AsyncSession,
        driver_repo,
        vehicle_repo,
        route_repo,
        assignment_repo,
        scenario_repo,
        controller: SimulationController | None = None,
    ) -> None:
        self._session = session
        self._drivers = driver_repo
        self._vehicles = vehicle_repo
        self._routes = route_repo
        self._assignments = assignment_repo
        self._scenarios = scenario_repo
        self._controller = controller

    def _controller_or_400(self) -> SimulationController:
        if self._controller is None:
            from fastapi import HTTPException

            raise HTTPException(
                status_code=503,
                detail="Simulation controller is not available",
            )
        return self._controller

    # ------------------------------------------------------------------
    # Drivers
    # ------------------------------------------------------------------

    async def create_driver(self, payload: schemas.DriverCreate) -> PersistedDriver:
        driver_id = payload.driver_id or str(uuid.uuid4())
        driver = await self._drivers.create(
            driver_id,
            payload.first_name,
            payload.last_name,
            license_number=payload.license_number,
            employment_status=payload.employment_status,
            behavior_profile=payload.behavior_profile,
        )
        await self._session.commit()
        return driver

    async def update_driver(
        self, driver_id: str, payload: schemas.DriverUpdate
    ) -> PersistedDriver | None:
        driver = await self._drivers.update(
            driver_id,
            first_name=payload.first_name,
            last_name=payload.last_name,
            license_number=payload.license_number,
            employment_status=payload.employment_status,
            behavior_profile=payload.behavior_profile,
        )
        if driver is not None:
            await self._session.commit()
        return driver

    async def delete_driver(self, driver_id: str) -> bool:
        deleted = await self._drivers.delete(driver_id)
        if deleted:
            await self._session.commit()
        return deleted

    async def list_drivers(self, limit: int, offset: int):
        return await self._drivers.list(limit, offset)

    # ------------------------------------------------------------------
    # Vehicles
    # ------------------------------------------------------------------

    async def create_vehicle(self, payload: schemas.VehicleCreate) -> PersistedVehicle:
        vehicle_id = payload.vehicle_id or str(uuid.uuid4())
        vehicle = await self._vehicles.create(
            vehicle_id,
            payload.manufacturer,
            payload.model,
            payload.year,
            registration_number=payload.registration_number,
            vin=payload.vin,
            fuel_type=payload.fuel_type,
            status=payload.status,
            display_name=payload.display_name,
            fuel_efficiency_factor=payload.fuel_efficiency_factor,
            acceleration_response=payload.acceleration_response,
            tank_capacity_liters=payload.tank_capacity_liters,
        )
        await self._session.commit()
        return vehicle

    async def update_vehicle(
        self, vehicle_id: str, payload: schemas.VehicleUpdate
    ) -> PersistedVehicle | None:
        vehicle = await self._vehicles.update(
            vehicle_id,
            registration_number=payload.registration_number,
            vin=payload.vin,
            manufacturer=payload.manufacturer,
            model=payload.model,
            year=payload.year,
            fuel_type=payload.fuel_type,
            status=payload.status,
            display_name=payload.display_name,
            fuel_efficiency_factor=payload.fuel_efficiency_factor,
            acceleration_response=payload.acceleration_response,
            tank_capacity_liters=payload.tank_capacity_liters,
        )
        if vehicle is not None:
            await self._session.commit()
        return vehicle

    async def delete_vehicle(self, vehicle_id: str) -> bool:
        deleted = await self._vehicles.delete(vehicle_id)
        if deleted:
            await self._session.commit()
        return deleted

    async def list_vehicles(self, limit: int, offset: int):
        return await self._vehicles.list(limit, offset)

    # ------------------------------------------------------------------
    # Routes
    # ------------------------------------------------------------------

    async def create_route(self, payload: schemas.RouteCreate) -> PersistedRoute:
        route_id = payload.route_id or str(uuid.uuid4())
        route = await self._routes.create(
            route_id,
            payload.name,
            payload.route_type,
            payload.origin,
            payload.destination,
            payload.estimated_distance_km,
            speed_limit_kmh=payload.speed_limit_kmh,
            is_active=payload.is_active,
        )
        await self._session.commit()
        return route

    async def update_route(
        self, route_id: str, payload: schemas.RouteUpdate
    ) -> PersistedRoute | None:
        route = await self._routes.update(
            route_id,
            name=payload.name,
            route_type=payload.route_type,
            origin=payload.origin,
            destination=payload.destination,
            estimated_distance_km=payload.estimated_distance_km,
            speed_limit_kmh=payload.speed_limit_kmh,
            is_active=payload.is_active,
        )
        if route is not None:
            await self._session.commit()
        return route

    async def delete_route(self, route_id: str) -> bool:
        deleted = await self._routes.delete(route_id)
        if deleted:
            await self._session.commit()
        return deleted

    async def list_routes(self, limit: int, offset: int):
        return await self._routes.list(limit, offset)

    # ------------------------------------------------------------------
    # Assignments
    # ------------------------------------------------------------------

    async def _validate_assignment_refs(
        self, driver_id: str, vehicle_id: str, route_id: str
    ) -> None:
        from fastapi import HTTPException

        if await self._drivers.get(driver_id) is None:
            raise HTTPException(status_code=404, detail=f"Driver {driver_id} not found")
        if await self._vehicles.get(vehicle_id) is None:
            raise HTTPException(status_code=404, detail=f"Vehicle {vehicle_id} not found")
        if await self._routes.get(route_id) is None:
            raise HTTPException(status_code=404, detail=f"Route {route_id} not found")

    async def create_assignment(
        self, payload: schemas.AssignmentCreate
    ) -> PersistedAssignment:
        from fastapi import HTTPException

        await self._validate_assignment_refs(
            payload.driver_id, payload.vehicle_id, payload.route_id
        )
        existing = await self._assignments.find_existing(
            payload.driver_id, payload.vehicle_id, payload.route_id
        )
        if existing is not None:
            raise HTTPException(
                status_code=409,
                detail=(
                    "An assignment for this driver/vehicle/route already exists"
                ),
            )
        assignment = await self._assignments.create(
            payload.assignment_id or str(uuid.uuid4()),
            payload.driver_id,
            payload.vehicle_id,
            payload.route_id,
            name=payload.name,
            notes=payload.notes,
            is_active=payload.is_active,
        )
        await self._session.commit()
        return assignment

    async def update_assignment(
        self, assignment_id: str, payload: schemas.AssignmentUpdate
    ) -> PersistedAssignment | None:
        if payload.driver_id or payload.vehicle_id or payload.route_id:
            current = await self._assignments.get(assignment_id)
            if current is None:
                return None
            driver_id = payload.driver_id or current.driver_id
            vehicle_id = payload.vehicle_id or current.vehicle_id
            route_id = payload.route_id or current.route_id
            await self._validate_assignment_refs(driver_id, vehicle_id, route_id)
        assignment = await self._assignments.update(
            assignment_id,
            driver_id=payload.driver_id,
            vehicle_id=payload.vehicle_id,
            route_id=payload.route_id,
            name=payload.name,
            notes=payload.notes,
            is_active=payload.is_active,
        )
        if assignment is not None:
            await self._session.commit()
        return assignment

    async def delete_assignment(self, assignment_id: str) -> bool:
        deleted = await self._assignments.delete(assignment_id)
        if deleted:
            await self._session.commit()
        return deleted

    async def list_assignments(self, is_active: bool | None = None):
        return await self._assignments.list(is_active=is_active)

    async def get_assignment(self, assignment_id: str) -> PersistedAssignment | None:
        return await self._assignments.get(assignment_id)

    # ------------------------------------------------------------------
    # Scenarios
    # ------------------------------------------------------------------

    async def create_scenario(
        self, payload: schemas.ScenarioCreate, assignment_ids: list[str] | None = None
    ) -> SimulationScenario:
        scenario = await self._scenarios.create(
            payload.name,
            description=payload.description,
            status=payload.status,
            duration_seconds=payload.duration_seconds,
            simulation_speed=payload.simulation_speed,
            seed=payload.seed,
        )
        if assignment_ids:
            await self.set_scenario_assignments(scenario.scenario_id, assignment_ids)
        else:
            await self._session.commit()
        return scenario

    async def update_scenario(
        self, scenario_id: str, payload: schemas.ScenarioUpdate
    ) -> SimulationScenario | None:
        scenario = await self._scenarios.get(scenario_id)
        if scenario is None:
            return None
        if scenario.status == "running":
            from fastapi import HTTPException

            raise HTTPException(
                status_code=409, detail="Cannot edit a running scenario"
            )
        if payload.status is not None and payload.status not in VALID_SCENARIO_STATUSES:
            from fastapi import HTTPException

            raise HTTPException(
                status_code=422, detail=f"Invalid scenario status: {payload.status}"
            )
        updated = await self._scenarios.update(
            scenario,
            name=payload.name,
            description=payload.description,
            status=payload.status,
            duration_seconds=payload.duration_seconds,
            simulation_speed=payload.simulation_speed,
            seed=payload.seed,
        )
        await self._session.commit()
        return updated
    async def delete_scenario(self, scenario_id: str) -> bool:
        scenario = await self._scenarios.get(scenario_id)
        if scenario is None:
            return False
        if scenario.status == "running":
            from fastapi import HTTPException

            raise HTTPException(
                status_code=409, detail="Cannot delete a running scenario"
            )
        deleted = await self._scenarios.delete(scenario_id)
        if deleted:
            await self._session.commit()
        return deleted

    async def get_scenario(self, scenario_id: str) -> SimulationScenario | None:
        return await self._scenarios.get(scenario_id)

    async def list_runs(
        self, scenario_id: str, limit: int, offset: int
    ) -> tuple[list[SimulationRun], int]:
        return await self._scenarios.runs.list_for_scenario(
            scenario_id, limit, offset
        )

    async def list_scenarios(self, limit: int, offset: int, status: str | None = None):
        return await self._scenarios.list(limit, offset, status=status)

    async def set_scenario_assignments(
        self, scenario_id: str, assignment_ids: list[str]
    ) -> SimulationScenario:
        from fastapi import HTTPException

        result = await self._session.execute(
            select(SimulationScenario)
            .where(SimulationScenario.scenario_id == scenario_id)
            .options(selectinload(SimulationScenario.assignments))
        )
        scenario = result.scalar_one_or_none()
        if scenario is None:
            raise HTTPException(status_code=404, detail=f"Scenario {scenario_id} not found")

        assignments = []
        for aid in assignment_ids:
            assignment = await self._assignments.get(aid)
            if assignment is None:
                raise HTTPException(status_code=404, detail=f"Assignment {aid} not found")
            assignments.append(assignment)

        scenario.assignments.clear()
        scenario.assignments.extend(assignments)
        await self._session.flush()
        await self._session.commit()
        return scenario

    async def activate_scenario(
        self, scenario_id: str
    ) -> SimulationScenario | None:
        """Transition a scenario to ``ready`` (arm for launch)."""
        result = await self._session.execute(
            select(SimulationScenario)
            .where(SimulationScenario.scenario_id == scenario_id)
            .options(selectinload(SimulationScenario.assignments))
        )
        scenario = result.scalar_one_or_none()
        if scenario is None:
            return None
        if scenario.status not in ("draft", "ready", "completed", "failed"):
            from fastapi import HTTPException

            raise HTTPException(
                status_code=409,
                detail=f"Scenario is in status '{scenario.status}' and cannot be armed",
            )
        if not scenario.assignments:
            from fastapi import HTTPException

            raise HTTPException(
                status_code=422,
                detail="Scenario has no assignments; add at least one before arming",
            )
        await self._scenarios.update(scenario, status="ready")
        await self._session.commit()
        return scenario

    # ------------------------------------------------------------------
    # Runs & launch
    # ------------------------------------------------------------------

    async def launch_scenario(
        self, scenario_id: str
    ) -> tuple[SimulationRun, dict]:
        from fastapi import HTTPException

        controller = self._controller_or_400()
        result = await self._session.execute(
            select(SimulationScenario)
            .where(SimulationScenario.scenario_id == scenario_id)
            .options(selectinload(SimulationScenario.assignments))
        )
        scenario = result.scalar_one_or_none()
        if scenario is None:
            raise HTTPException(status_code=404, detail=f"Scenario {scenario_id} not found")
        if scenario.status != "ready":
            raise HTTPException(
                status_code=409,
                detail=f"Only a 'ready' scenario can be launched (status={scenario.status})",
            )
        if not scenario.assignments:
            raise HTTPException(
                status_code=422, detail="Scenario has no active assignments to simulate"
            )

        driver_map = {
            d.driver_id: d
            for d in await self._load_entities(
                {a.driver_id for a in scenario.assignments},
                PersistedDriver,
                "driver_id",
            )
        }
        vehicle_map = {
            v.vehicle_id: v
            for v in await self._load_entities(
                {a.vehicle_id for a in scenario.assignments},
                PersistedVehicle,
                "vehicle_id",
            )
        }
        route_map = {
            r.route_id: r
            for r in await self._load_entities(
                {a.route_id for a in scenario.assignments},
                PersistedRoute,
                "route_id",
            )
        }

        config = build_fleet_configuration(
            list(scenario.assignments),
            drivers=driver_map,
            vehicles=vehicle_map,
            routes=route_map,
        )
        if not config.assignments:
            raise HTTPException(
                status_code=422,
                detail="None of the scenario's assignments could be resolved into a fleet",
            )

        run = await self._scenarios.runs.create(
            scenario.scenario_id,
            status="running",
            seed=scenario.seed,
        )
        await self._scenarios.update(scenario, status="running")
        await self._session.commit()

        status = await controller.launch(
            config,
            scenario_id=scenario.scenario_id,
            scenario_name=scenario.name,
            run_id=run.run_id,
            seed=scenario.seed,
        )
        return run, status

    async def stop_scenario(self, scenario_id: str) -> dict | None:
        from fastapi import HTTPException

        controller = self._controller_or_400()
        scenario = await self._scenarios.get(scenario_id)
        if scenario is None:
            return None

        status = await controller.stop()

        if scenario.status == "running":
            await self._scenarios.update(scenario, status="ready")
            latest_run = await self._scenarios.runs.latest_for_scenario(scenario_id)
            if latest_run is not None and latest_run.status == "running":
                from datetime import datetime, timezone

                await self._scenarios.runs.update(
                    latest_run,
                    status="stopped",
                    end_time=datetime.now(timezone.utc),
                )
            await self._session.commit()
        return status

    async def reset(self) -> dict:
        controller = self._controller_or_400()
        return await controller.reset()

    async def status(self) -> dict:
        if self._controller is None:
            return {
                "running": False,
                "scenario_id": None,
                "scenario_name": None,
                "run_id": None,
                "started_at": None,
                "vehicles": 0,
            }
        return self._controller.status()

    async def complete_active_runs(self) -> None:
        """Mark any running scenario/run as stopped/failed on shutdown.

        Best-effort; used by the app teardown so the persisted lifecycle
        tracks reality.
        """
        result = await self._session.execute(
            select(SimulationRun).where(SimulationRun.status == "running")
        )
        for run in result.scalars().all():
            await self._scenarios.runs.update(
                run,
                status="stopped",
            )
            scenario = await self._scenarios.get(run.scenario_id)
            if scenario is not None and scenario.status == "running":
                await self._scenarios.update(scenario, status="ready")
        await self._session.commit()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _load_entities(self, ids: set[str], model, id_col: str):
        if not ids:
            return []
        result = await self._session.execute(
            select(model).where(getattr(model, id_col).in_(list(ids)))
        )
        return result.scalars().all()
