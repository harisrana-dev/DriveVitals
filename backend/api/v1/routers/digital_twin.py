"""Digital Twin Lab router (admin-only).

Manage the fleet (drivers, vehicles, routes), assignments, simulation
scenarios and their runs, and launch/stop/reset scenario simulations.

Every endpoint requires an authenticated administrator; non-admins
receive 403, unauthenticated requests 401.
"""

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.api.v1.dependencies import (
    get_digital_twin_service,
    require_admin,
)
from backend.api.v1.schemas.common import PaginatedResponse, Response
from backend.api.v1.schemas.digital_twin import (
    AssignmentCreate,
    AssignmentRead,
    AssignmentUpdate,
    DriverCreate,
    DriverManagementRead,
    DriverUpdate,
    RouteCreate,
    RouteManagementRead,
    RouteUpdate,
    RunRead,
    ScenarioCreate,
    ScenarioRead,
    ScenarioUpdate,
    SimulationStatus,
    VehicleCreate,
    VehicleManagementRead,
    VehicleUpdate,
)
from backend.api.v1.services.digital_twin_service import DigitalTwinService
from backend.db.models.user import User

router = APIRouter(prefix="/digital-twin")


# ---------------------------------------------------------------------------
# Simulation status / lifecycle
# ---------------------------------------------------------------------------

@router.get(
    "/status",
    response_model=Response[SimulationStatus],
    summary="Simulation controller status",
    description="Report whether a scenario simulation is currently running.",
    tags=["Digital Twin"],
)
async def simulation_status(
    current_user: User = Depends(require_admin),
    service: DigitalTwinService = Depends(get_digital_twin_service),
) -> Response[SimulationStatus]:
    return Response[SimulationStatus](data=SimulationStatus(**await service.status()))


@router.post(
    "/scenarios/{scenario_id}/launch",
    response_model=Response[dict],
    summary="Launch a scenario",
    description="Start a simulation run for a 'ready' scenario.",
    tags=["Digital Twin"],
)
async def launch_scenario(
    scenario_id: str,
    current_user: User = Depends(require_admin),
    service: DigitalTwinService = Depends(get_digital_twin_service),
) -> Response[dict]:
    run, status = await service.launch_scenario(scenario_id)
    return Response[dict](data={"run_id": run.run_id, "status": status})


@router.post(
    "/scenarios/{scenario_id}/stop",
    response_model=Response[SimulationStatus],
    summary="Stop a scenario",
    description="Stop a running scenario simulation.",
    tags=["Digital Twin"],
)
async def stop_scenario(
    scenario_id: str,
    current_user: User = Depends(require_admin),
    service: DigitalTwinService = Depends(get_digital_twin_service),
) -> Response[SimulationStatus]:
    status = await service.stop_scenario(scenario_id)
    if status is None:
        raise HTTPException(status_code=404, detail=f"Scenario {scenario_id} not found")
    return Response[SimulationStatus](data=SimulationStatus(**status))


@router.post(
    "/reset",
    response_model=Response[SimulationStatus],
    summary="Reset the simulation",
    description="Stop any run and restore the default fleet.",
    tags=["Digital Twin"],
)
async def reset_simulation(
    current_user: User = Depends(require_admin),
    service: DigitalTwinService = Depends(get_digital_twin_service),
) -> Response[SimulationStatus]:
    return Response[SimulationStatus](data=SimulationStatus(**await service.reset()))


# ---------------------------------------------------------------------------
# Drivers (admin management)
# ---------------------------------------------------------------------------

@router.get(
    "/drivers",
    response_model=PaginatedResponse[DriverManagementRead],
    tags=["Digital Twin"],
)
async def list_managed_drivers(
    limit: int = Query(default=100),
    offset: int = Query(default=0),
    current_user: User = Depends(require_admin),
    service: DigitalTwinService = Depends(get_digital_twin_service),
) -> PaginatedResponse[DriverManagementRead]:
    drivers, count = await service.list_drivers(limit, offset)
    return PaginatedResponse[DriverManagementRead](
        data=[DriverManagementRead.model_validate(d) for d in drivers], count=count
    )


@router.post(
    "/drivers",
    response_model=Response[DriverManagementRead],
    tags=["Digital Twin"],
)
async def create_managed_driver(
    payload: DriverCreate,
    current_user: User = Depends(require_admin),
    service: DigitalTwinService = Depends(get_digital_twin_service),
) -> Response[DriverManagementRead]:
    driver = await service.create_driver(payload)
    return Response[DriverManagementRead](data=DriverManagementRead.model_validate(driver))


@router.patch(
    "/drivers/{driver_id}",
    response_model=Response[DriverManagementRead],
    tags=["Digital Twin"],
)
async def update_managed_driver(
    driver_id: str,
    payload: DriverUpdate,
    current_user: User = Depends(require_admin),
    service: DigitalTwinService = Depends(get_digital_twin_service),
) -> Response[DriverManagementRead]:
    driver = await service.update_driver(driver_id, payload)
    if driver is None:
        raise HTTPException(status_code=404, detail=f"Driver {driver_id} not found")
    return Response[DriverManagementRead](data=DriverManagementRead.model_validate(driver))


@router.delete(
    "/drivers/{driver_id}",
    response_model=Response[dict],
    tags=["Digital Twin"],
)
async def delete_managed_driver(
    driver_id: str,
    current_user: User = Depends(require_admin),
    service: DigitalTwinService = Depends(get_digital_twin_service),
) -> Response[dict]:
    deleted = await service.delete_driver(driver_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Driver {driver_id} not found")
    return Response[dict](data={"deleted": driver_id})


# ---------------------------------------------------------------------------
# Vehicles (admin management)
# ---------------------------------------------------------------------------

@router.get(
    "/vehicles",
    response_model=PaginatedResponse[VehicleManagementRead],
    tags=["Digital Twin"],
)
async def list_managed_vehicles(
    limit: int = Query(default=100),
    offset: int = Query(default=0),
    current_user: User = Depends(require_admin),
    service: DigitalTwinService = Depends(get_digital_twin_service),
) -> PaginatedResponse[VehicleManagementRead]:
    vehicles, count = await service.list_vehicles(limit, offset)
    return PaginatedResponse[VehicleManagementRead](
        data=[VehicleManagementRead.model_validate(v) for v in vehicles], count=count
    )


@router.post(
    "/vehicles",
    response_model=Response[VehicleManagementRead],
    tags=["Digital Twin"],
)
async def create_managed_vehicle(
    payload: VehicleCreate,
    current_user: User = Depends(require_admin),
    service: DigitalTwinService = Depends(get_digital_twin_service),
) -> Response[VehicleManagementRead]:
    vehicle = await service.create_vehicle(payload)
    return Response[VehicleManagementRead](data=VehicleManagementRead.model_validate(vehicle))


@router.patch(
    "/vehicles/{vehicle_id}",
    response_model=Response[VehicleManagementRead],
    tags=["Digital Twin"],
)
async def update_managed_vehicle(
    vehicle_id: str,
    payload: VehicleUpdate,
    current_user: User = Depends(require_admin),
    service: DigitalTwinService = Depends(get_digital_twin_service),
) -> Response[VehicleManagementRead]:
    vehicle = await service.update_vehicle(vehicle_id, payload)
    if vehicle is None:
        raise HTTPException(status_code=404, detail=f"Vehicle {vehicle_id} not found")
    return Response[VehicleManagementRead](data=VehicleManagementRead.model_validate(vehicle))


@router.delete(
    "/vehicles/{vehicle_id}",
    response_model=Response[dict],
    tags=["Digital Twin"],
)
async def delete_managed_vehicle(
    vehicle_id: str,
    current_user: User = Depends(require_admin),
    service: DigitalTwinService = Depends(get_digital_twin_service),
) -> Response[dict]:
    deleted = await service.delete_vehicle(vehicle_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Vehicle {vehicle_id} not found")
    return Response[dict](data={"deleted": vehicle_id})


# ---------------------------------------------------------------------------
# Routes (admin management)
# ---------------------------------------------------------------------------

@router.get(
    "/routes",
    response_model=PaginatedResponse[RouteManagementRead],
    tags=["Digital Twin"],
)
async def list_managed_routes(
    limit: int = Query(default=100),
    offset: int = Query(default=0),
    current_user: User = Depends(require_admin),
    service: DigitalTwinService = Depends(get_digital_twin_service),
) -> PaginatedResponse[RouteManagementRead]:
    routes, count = await service.list_routes(limit, offset)
    return PaginatedResponse[RouteManagementRead](
        data=[RouteManagementRead.model_validate(r) for r in routes], count=count
    )


@router.post(
    "/routes",
    response_model=Response[RouteManagementRead],
    tags=["Digital Twin"],
)
async def create_managed_route(
    payload: RouteCreate,
    current_user: User = Depends(require_admin),
    service: DigitalTwinService = Depends(get_digital_twin_service),
) -> Response[RouteManagementRead]:
    route = await service.create_route(payload)
    return Response[RouteManagementRead](data=RouteManagementRead.model_validate(route))


@router.patch(
    "/routes/{route_id}",
    response_model=Response[RouteManagementRead],
    tags=["Digital Twin"],
)
async def update_managed_route(
    route_id: str,
    payload: RouteUpdate,
    current_user: User = Depends(require_admin),
    service: DigitalTwinService = Depends(get_digital_twin_service),
) -> Response[RouteManagementRead]:
    route = await service.update_route(route_id, payload)
    if route is None:
        raise HTTPException(status_code=404, detail=f"Route {route_id} not found")
    return Response[RouteManagementRead](data=RouteManagementRead.model_validate(route))


@router.delete(
    "/routes/{route_id}",
    response_model=Response[dict],
    tags=["Digital Twin"],
)
async def delete_managed_route(
    route_id: str,
    current_user: User = Depends(require_admin),
    service: DigitalTwinService = Depends(get_digital_twin_service),
) -> Response[dict]:
    deleted = await service.delete_route(route_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Route {route_id} not found")
    return Response[dict](data={"deleted": route_id})


# ---------------------------------------------------------------------------
# Assignments
# ---------------------------------------------------------------------------

@router.get(
    "/assignments",
    response_model=Response[list[AssignmentRead]],
    tags=["Digital Twin"],
)
async def list_assignments(
    is_active: bool | None = None,
    current_user: User = Depends(require_admin),
    service: DigitalTwinService = Depends(get_digital_twin_service),
) -> Response[list[AssignmentRead]]:
    assignments = await service.list_assignments(is_active=is_active)
    return Response[list[AssignmentRead]](
        data=[AssignmentRead.model_validate(a) for a in assignments]
    )


@router.post(
    "/assignments",
    response_model=Response[AssignmentRead],
    tags=["Digital Twin"],
)
async def create_assignment(
    payload: AssignmentCreate,
    current_user: User = Depends(require_admin),
    service: DigitalTwinService = Depends(get_digital_twin_service),
) -> Response[AssignmentRead]:
    assignment = await service.create_assignment(payload)
    return Response[AssignmentRead](data=AssignmentRead.model_validate(assignment))


@router.patch(
    "/assignments/{assignment_id}",
    response_model=Response[AssignmentRead],
    tags=["Digital Twin"],
)
async def update_assignment(
    assignment_id: str,
    payload: AssignmentUpdate,
    current_user: User = Depends(require_admin),
    service: DigitalTwinService = Depends(get_digital_twin_service),
) -> Response[AssignmentRead]:
    assignment = await service.update_assignment(assignment_id, payload)
    if assignment is None:
        raise HTTPException(
            status_code=404, detail=f"Assignment {assignment_id} not found"
        )
    return Response[AssignmentRead](data=AssignmentRead.model_validate(assignment))


@router.delete(
    "/assignments/{assignment_id}",
    response_model=Response[dict],
    tags=["Digital Twin"],
)
async def delete_assignment(
    assignment_id: str,
    current_user: User = Depends(require_admin),
    service: DigitalTwinService = Depends(get_digital_twin_service),
) -> Response[dict]:
    deleted = await service.delete_assignment(assignment_id)
    if not deleted:
        raise HTTPException(
            status_code=404, detail=f"Assignment {assignment_id} not found"
        )
    return Response[dict](data={"deleted": assignment_id})


# ---------------------------------------------------------------------------
# Scenarios & runs
# ---------------------------------------------------------------------------

@router.get(
    "/scenarios",
    response_model=PaginatedResponse[ScenarioRead],
    tags=["Digital Twin"],
)
async def list_scenarios(
    limit: int = Query(default=100),
    offset: int = Query(default=0),
    status: str | None = None,
    current_user: User = Depends(require_admin),
    service: DigitalTwinService = Depends(get_digital_twin_service),
) -> PaginatedResponse[ScenarioRead]:
    scenarios, count = await service.list_scenarios(limit, offset, status=status)
    return PaginatedResponse[ScenarioRead](
        data=[ScenarioRead.model_validate(s) for s in scenarios], count=count
    )


@router.post(
    "/scenarios",
    response_model=Response[ScenarioRead],
    tags=["Digital Twin"],
)
async def create_scenario(
    payload: ScenarioCreate,
    assignment_ids: list[str] | None = Query(default=None),
    current_user: User = Depends(require_admin),
    service: DigitalTwinService = Depends(get_digital_twin_service),
) -> Response[ScenarioRead]:
    scenario = await service.create_scenario(
        payload, assignment_ids=assignment_ids or []
    )
    return Response[ScenarioRead](data=ScenarioRead.model_validate(scenario))


@router.get(
    "/scenarios/{scenario_id}",
    response_model=Response[ScenarioRead],
    tags=["Digital Twin"],
)
async def get_scenario(
    scenario_id: str,
    current_user: User = Depends(require_admin),
    service: DigitalTwinService = Depends(get_digital_twin_service),
) -> Response[ScenarioRead]:
    scenario = await service.get_scenario(scenario_id)
    if scenario is None:
        raise HTTPException(status_code=404, detail=f"Scenario {scenario_id} not found")
    return Response[ScenarioRead](data=ScenarioRead.model_validate(scenario))


@router.patch(
    "/scenarios/{scenario_id}",
    response_model=Response[ScenarioRead],
    tags=["Digital Twin"],
)
async def update_scenario(
    scenario_id: str,
    payload: ScenarioUpdate,
    current_user: User = Depends(require_admin),
    service: DigitalTwinService = Depends(get_digital_twin_service),
) -> Response[ScenarioRead]:
    scenario = await service.update_scenario(scenario_id, payload)
    if scenario is None:
        raise HTTPException(status_code=404, detail=f"Scenario {scenario_id} not found")
    return Response[ScenarioRead](data=ScenarioRead.model_validate(scenario))


@router.post(
    "/scenarios/{scenario_id}/assignments",
    response_model=Response[ScenarioRead],
    tags=["Digital Twin"],
)
async def set_scenario_assignments(
    scenario_id: str,
    assignment_ids: list[str],
    current_user: User = Depends(require_admin),
    service: DigitalTwinService = Depends(get_digital_twin_service),
) -> Response[ScenarioRead]:
    scenario = await service.set_scenario_assignments(scenario_id, assignment_ids)
    return Response[ScenarioRead](data=ScenarioRead.model_validate(scenario))


@router.post(
    "/scenarios/{scenario_id}/activate",
    response_model=Response[ScenarioRead],
    tags=["Digital Twin"],
)
async def activate_scenario(
    scenario_id: str,
    current_user: User = Depends(require_admin),
    service: DigitalTwinService = Depends(get_digital_twin_service),
) -> Response[ScenarioRead]:
    scenario = await service.activate_scenario(scenario_id)
    if scenario is None:
        raise HTTPException(status_code=404, detail=f"Scenario {scenario_id} not found")
    return Response[ScenarioRead](data=ScenarioRead.model_validate(scenario))


@router.delete(
    "/scenarios/{scenario_id}",
    response_model=Response[dict],
    tags=["Digital Twin"],
)
async def delete_scenario(
    scenario_id: str,
    current_user: User = Depends(require_admin),
    service: DigitalTwinService = Depends(get_digital_twin_service),
) -> Response[dict]:
    deleted = await service.delete_scenario(scenario_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Scenario {scenario_id} not found")
    return Response[dict](data={"deleted": scenario_id})


@router.get(
    "/scenarios/{scenario_id}/runs",
    response_model=PaginatedResponse[RunRead],
    tags=["Digital Twin"],
)
async def list_runs_for_scenario(
    scenario_id: str,
    limit: int = Query(default=100),
    offset: int = Query(default=0),
    current_user: User = Depends(require_admin),
    service: DigitalTwinService = Depends(get_digital_twin_service),
) -> PaginatedResponse[RunRead]:
    # Validate scenario exists.
    scenario = await service.get_scenario(scenario_id)
    if scenario is None:
        raise HTTPException(status_code=404, detail=f"Scenario {scenario_id} not found")
    runs, count = await service.list_runs(scenario_id, limit, offset)
    return PaginatedResponse[RunRead](
        data=[RunRead.model_validate(r) for r in runs], count=count
    )
