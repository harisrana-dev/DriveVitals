"""API tests for the Digital Twin Lab (admin-only).

Verifies authorization guards and the managed CRUD + scenario lifecycle
surface. Launch/stop/reset require a wired simulation controller, which
the API test harness does not provide; those return 503 here and are
exercised directly against the controller in the integration suite.
"""

import pytest
from sqlalchemy import select

from backend.api import simulation_state


@pytest.fixture(autouse=True)
def _no_controller():
    """Keep the controller unwired for these API tests.

    Launch/stop/reset require a live simulation controller; the API test
    harness never wires one, so those endpoints return 503. Pinning the
    controller to ``None`` here keeps every test in this module hermetic
    even if another module imports ``backend.api.main`` (which wires the
    controller at import time) earlier in the same pytest process.
    """
    original = simulation_state.simulation_controller
    simulation_state.simulation_controller = None
    try:
        yield
    finally:
        simulation_state.simulation_controller = original


# ---------------------------------------------------------------------------
# Authorization guards
# ---------------------------------------------------------------------------

async def _do(client, method, url, **kwargs):
    return await client.request(method, url, **kwargs)


async def test_status_requires_authentication(client):
    resp = await client.get("/api/v1/digital-twin/status")
    assert resp.status_code == 401


async def test_status_forbidden_for_non_admin(operator_client, viewer_client):
    for c in (operator_client, viewer_client):
        resp = await c.get("/api/v1/digital-twin/status")
        assert resp.status_code == 403


async def test_status_ok_for_admin(admin_client):
    resp = await admin_client.get("/api/v1/digital-twin/status")
    assert resp.status_code == 200
    body = resp.json()["data"]
    assert body["running"] is False
    assert "vehicles" in body


async def test_management_endpoints_require_admin(operator_client):
    resp = await operator_client.get("/api/v1/digital-twin/drivers")
    assert resp.status_code == 403
    resp = await operator_client.get("/api/v1/digital-twin/vehicles")
    assert resp.status_code == 403
    resp = await operator_client.get("/api/v1/digital-twin/routes")
    assert resp.status_code == 403
    resp = await operator_client.get("/api/v1/digital-twin/assignments")
    assert resp.status_code == 403
    resp = await operator_client.get("/api/v1/digital-twin/scenarios")
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Driver management
# ---------------------------------------------------------------------------

async def test_create_and_list_driver(admin_client):
    resp = await admin_client.post(
        "/api/v1/digital-twin/drivers",
        json={
            "driver_id": "dt-d-1",
            "first_name": "Zeina",
            "last_name": "Khan",
            "license_number": "DT-LIC-1",
            "behavior_profile": "eco",
        },
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["driver_id"] == "dt-d-1"
    assert data["behavior_profile"] == "eco"

    resp = await admin_client.get("/api/v1/digital-twin/drivers")
    assert resp.status_code == 200
    ids = [d["driver_id"] for d in resp.json()["data"]]
    assert "dt-d-1" in ids


async def test_update_and_delete_driver(admin_client):
    await admin_client.post(
        "/api/v1/digital-twin/drivers",
        json={
            "driver_id": "dt-d-2",
            "first_name": "Omar",
            "last_name": "Ali",
            "license_number": "DT-LIC-2",
        },
    )
    resp = await admin_client.patch(
        "/api/v1/digital-twin/drivers/dt-d-2",
        json={"behavior_profile": "aggressive"},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["behavior_profile"] == "aggressive"

    resp = await admin_client.delete("/api/v1/digital-twin/drivers/dt-d-2")
    assert resp.status_code == 200

    resp = await admin_client.patch(
        "/api/v1/digital-twin/drivers/dt-d-2", json={"first_name": "X"}
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Vehicle management
# ---------------------------------------------------------------------------

async def test_create_and_update_vehicle(admin_client):
    resp = await admin_client.post(
        "/api/v1/digital-twin/vehicles",
        json={
            "vehicle_id": "dt-v-1",
            "registration_number": "DT-REG-1",
            "vin": "DTVIN00000000001",
            "manufacturer": "Ford",
            "model": "Transit",
            "year": 2024,
            "fuel_type": "diesel",
            "fuel_efficiency_factor": 0.9,
            "acceleration_response": 1.2,
            "tank_capacity_liters": 80.0,
        },
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["fuel_efficiency_factor"] == 0.9
    assert data["tank_capacity_liters"] == 80.0

    resp = await admin_client.patch(
        "/api/v1/digital-twin/vehicles/dt-v-1",
        json={"display_name": "Van A", "acceleration_response": 1.5},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["display_name"] == "Van A"
    assert resp.json()["data"]["acceleration_response"] == 1.5


# ---------------------------------------------------------------------------
# Route management
# ---------------------------------------------------------------------------

async def test_create_and_update_route(admin_client):
    resp = await admin_client.post(
        "/api/v1/digital-twin/routes",
        json={
            "route_id": "dt-r-1",
            "name": "Test Route",
            "route_type": "urban",
            "origin": "A",
            "destination": "B",
            "estimated_distance_km": 10.0,
            "speed_limit_kmh": 50.0,
        },
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["speed_limit_kmh"] == 50.0

    resp = await admin_client.patch(
        "/api/v1/digital-twin/routes/dt-r-1", json={"is_active": False}
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["is_active"] is False


# ---------------------------------------------------------------------------
# Assignments
# ---------------------------------------------------------------------------

@pytest.fixture
async def fleet_ids(admin_client) -> dict:
    """Create a driver/vehicle/route and return their ids."""
    dr = (await admin_client.post("/api/v1/digital-twin/drivers",
          json={"driver_id": "assign-d", "first_name": "A", "last_name": "B",
                "license_number": "ASSIGN-LIC"})).json()["data"]["driver_id"]
    ve = (await admin_client.post("/api/v1/digital-twin/vehicles",
          json={"vehicle_id": "assign-v", "registration_number": "ASSIGN-REG",
                "vin": "ASSIGNVIN00000001", "manufacturer": "M", "model": "Mo",
                "year": 2024})).json()["data"]["vehicle_id"]
    ro = (await admin_client.post("/api/v1/digital-twin/routes",
          json={"route_id": "assign-r", "name": "AR", "route_type": "urban",
                "origin": "O", "destination": "D", "estimated_distance_km": 5.0,
                "speed_limit_kmh": 60.0})).json()["data"]["route_id"]
    return {"driver": dr, "vehicle": ve, "route": ro}


async def test_assignment_crud(fleet_ids, admin_client):
    resp = await admin_client.post(
        "/api/v1/digital-twin/assignments",
        json={
            "assignment_id": "assign-a-1",
            "driver_id": fleet_ids["driver"],
            "vehicle_id": fleet_ids["vehicle"],
            "route_id": fleet_ids["route"],
        },
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["assignment_id"] == "assign-a-1"

    # duplicate triple -> 409
    resp = await admin_client.post(
        "/api/v1/digital-twin/assignments",
        json={
            "driver_id": fleet_ids["driver"],
            "vehicle_id": fleet_ids["vehicle"],
            "route_id": fleet_ids["route"],
        },
    )
    assert resp.status_code == 409

    # unknown reference -> 404
    resp = await admin_client.post(
        "/api/v1/digital-twin/assignments",
        json={
            "driver_id": "nope",
            "vehicle_id": fleet_ids["vehicle"],
            "route_id": fleet_ids["route"],
        },
    )
    assert resp.status_code == 404

    # deactivate then delete
    resp = await admin_client.patch(
        "/api/v1/digital-twin/assignments/assign-a-1", json={"is_active": False}
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["is_active"] is False

    resp = await admin_client.delete("/api/v1/digital-twin/assignments/assign-a-1")
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------

async def test_scenario_lifecycle(fleet_ids, admin_client):
    # create scenario
    resp = await admin_client.post(
        "/api/v1/digital-twin/scenarios",
        json={"name": "Test Scenario", "description": "desc", "seed": 42},
    )
    assert resp.status_code == 200, resp.text
    scenario_id = resp.json()["data"]["scenario_id"]
    assert resp.json()["data"]["status"] == "draft"

    # create assignment first
    await admin_client.post(
        "/api/v1/digital-twin/assignments",
        json={
            "assignment_id": "scen-a-1",
            "driver_id": fleet_ids["driver"],
            "vehicle_id": fleet_ids["vehicle"],
            "route_id": fleet_ids["route"],
        },
    )

    # set assignments
    resp = await admin_client.post(
        f"/api/v1/digital-twin/scenarios/{scenario_id}/assignments",
        json=["scen-a-1"],
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["assignment_ids"] == ["scen-a-1"]

    # GET individual scenario serializes assignment_ids
    resp = await admin_client.get(f"/api/v1/digital-twin/scenarios/{scenario_id}")
    assert resp.status_code == 200
    assert resp.json()["data"]["assignment_ids"] == ["scen-a-1"]

    # activate requires at least one assignment; it has one -> ready
    resp = await admin_client.post(
        f"/api/v1/digital-twin/scenarios/{scenario_id}/activate"
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["status"] == "ready"
    assert resp.json()["data"]["assignment_ids"] == ["scen-a-1"]

    # cannot edit a scenario with invalid status
    resp = await admin_client.patch(
        f"/api/v1/digital-twin/scenarios/{scenario_id}",
        json={"status": "bogus"},
    )
    assert resp.status_code == 422

    # list scenarios — verify assignment_ids present in the list response
    resp = await admin_client.get("/api/v1/digital-twin/scenarios")
    assert resp.status_code == 200
    scenarios = resp.json()["data"]
    names = [s["name"] for s in scenarios]
    assert "Test Scenario" in names
    listed = next(s for s in scenarios if s["scenario_id"] == scenario_id)
    assert listed["assignment_ids"] == ["scen-a-1"]

    # runs endpoint lists (empty)
    resp = await admin_client.get(f"/api/v1/digital-twin/scenarios/{scenario_id}/runs")
    assert resp.status_code == 200

    # delete scenario (it is 'ready', not running) -> ok
    resp = await admin_client.delete(f"/api/v1/digital-twin/scenarios/{scenario_id}")
    assert resp.status_code == 200


async def test_activate_requires_assignments(admin_client):
    resp = await admin_client.post(
        "/api/v1/digital-twin/scenarios",
        json={"name": "Empty Scenario"},
    )
    scenario_id = resp.json()["data"]["scenario_id"]
    resp = await admin_client.post(
        f"/api/v1/digital-twin/scenarios/{scenario_id}/activate"
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Launch requires a controller
# ---------------------------------------------------------------------------

async def test_launch_unavailable_without_controller(fleet_ids, admin_client):
    resp = await admin_client.post(
        "/api/v1/digital-twin/scenarios",
        json={"name": "Launch Scenario", "seed": 1},
    )
    scenario_id = resp.json()["data"]["scenario_id"]
    await admin_client.post(
        "/api/v1/digital-twin/assignments",
        json={
            "driver_id": fleet_ids["driver"],
            "vehicle_id": fleet_ids["vehicle"],
            "route_id": fleet_ids["route"],
        },
    )
    await admin_client.post(
        f"/api/v1/digital-twin/scenarios/{scenario_id}/activate"
    )
    # controller not wired in this harness -> 503
    resp = await admin_client.post(
        f"/api/v1/digital-twin/scenarios/{scenario_id}/launch"
    )
    assert resp.status_code == 503


# ---------------------------------------------------------------------------
# Assignment-serialization regression
# ---------------------------------------------------------------------------


async def test_scenario_read_serializes_persisted_assignments(fleet_ids, admin_client):
    """ScenarioRead must surface persisted assignment_ids (not []).

    Reproduces the exact failure mode from the forensic audit: DB had a
    persisted scenario→assignment link but the API returned assignment_ids=[].
    """
    resp = await admin_client.post(
        "/api/v1/digital-twin/assignments",
        json={
            "assignment_id": "regression-a-1",
            "driver_id": fleet_ids["driver"],
            "vehicle_id": fleet_ids["vehicle"],
            "route_id": fleet_ids["route"],
        },
    )
    assert resp.status_code == 200, resp.text

    # Create scenario with assignment via query param
    resp = await admin_client.post(
        "/api/v1/digital-twin/scenarios?assignment_ids=regression-a-1",
        json={"name": "Regression Scenario", "seed": 1},
    )
    assert resp.status_code == 200, resp.text
    scenario_id = resp.json()["data"]["scenario_id"]
    assert resp.json()["data"]["assignment_ids"] == ["regression-a-1"]

    # Single-get serializes assignment_ids
    resp = await admin_client.get(f"/api/v1/digital-twin/scenarios/{scenario_id}")
    assert resp.status_code == 200
    assert resp.json()["data"]["assignment_ids"] == ["regression-a-1"]

    # List serializes assignment_ids
    resp = await admin_client.get("/api/v1/digital-twin/scenarios")
    assert resp.status_code == 200
    target = next(s for s in resp.json()["data"] if s["scenario_id"] == scenario_id)
    assert target["assignment_ids"] == ["regression-a-1"]


async def test_scenario_without_assignments_returns_empty_assignment_ids(admin_client):
    """A scenario with no assignments must return assignment_ids == []."""
    resp = await admin_client.post(
        "/api/v1/digital-twin/scenarios",
        json={"name": "No Fleet Scenario"},
    )
    assert resp.status_code == 200
    scenario_id = resp.json()["data"]["scenario_id"]
    assert resp.json()["data"]["assignment_ids"] == []

    # Single-get
    resp = await admin_client.get(f"/api/v1/digital-twin/scenarios/{scenario_id}")
    assert resp.status_code == 200
    assert resp.json()["data"]["assignment_ids"] == []

    # List
    resp = await admin_client.get("/api/v1/digital-twin/scenarios")
    target = next(s for s in resp.json()["data"] if s["scenario_id"] == scenario_id)
    assert target["assignment_ids"] == []


# ---------------------------------------------------------------------------
# Scenario-delete FK regression
# ---------------------------------------------------------------------------


async def test_delete_scenario_removes_child_runs(fleet_ids, admin_client, session):
    """Deleting a scenario must also delete its historical SimulationRun records.

    Reproduces the FK violation from the forensic audit: the DB rejected
    DELETE FROM simulation_scenarios because simulation_runs.scenario_id
    still referenced the row.
    """
    from backend.db.models.scenario import SimulationRun

    # Create scenario with an assignment so it can be activated
    await admin_client.post(
        "/api/v1/digital-twin/assignments",
        json={
            "assignment_id": "del-a-1",
            "driver_id": fleet_ids["driver"],
            "vehicle_id": fleet_ids["vehicle"],
            "route_id": fleet_ids["route"],
        },
    )
    resp = await admin_client.post(
        "/api/v1/digital-twin/scenarios?assignment_ids=del-a-1",
        json={"name": "Delete Me Scenario", "seed": 1},
    )
    assert resp.status_code == 200, resp.text
    scenario_id = resp.json()["data"]["scenario_id"]

    # Insert a SimulationRun directly (launch requires a wired controller)
    run = SimulationRun(
        scenario_id=scenario_id,
        status="completed",
        seed=42,
        vehicles_active=3,
        trips_completed=10,
    )
    session.add(run)
    await session.flush()
    run_id = run.run_id

    # Commit so the API session (separate connection) can see the run
    await session.commit()

    # Confirm the run exists via the API
    resp = await admin_client.get(
        f"/api/v1/digital-twin/scenarios/{scenario_id}/runs"
    )
    assert resp.status_code == 200
    assert resp.json()["count"] == 1

    # Delete the scenario — must NOT raise FK violation
    resp = await admin_client.delete(
        f"/api/v1/digital-twin/scenarios/{scenario_id}"
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["deleted"] == scenario_id

    # Scenario is gone
    resp = await admin_client.get(f"/api/v1/digital-twin/scenarios/{scenario_id}")
    assert resp.status_code == 404

    # Run is gone (no orphaned rows)
    from sqlalchemy import select

    result = await session.execute(
        select(SimulationRun).where(SimulationRun.run_id == run_id)
    )
    assert result.scalar_one_or_none() is None


async def test_delete_scenario_without_runs_succeeds(admin_client, session):
    """Deleting a scenario that has no runs must succeed (no FK issue)."""

    resp = await admin_client.post(
        "/api/v1/digital-twin/scenarios",
        json={"name": "Empty Delete Scenario"},
    )
    assert resp.status_code == 200
    scenario_id = resp.json()["data"]["scenario_id"]

    # Confirm no runs
    resp = await admin_client.get(
        f"/api/v1/digital-twin/scenarios/{scenario_id}/runs"
    )
    assert resp.json()["count"] == 0

    # Delete succeeds
    resp = await admin_client.delete(
        f"/api/v1/digital-twin/scenarios/{scenario_id}"
    )
    assert resp.status_code == 200, resp.text

    # Confirm gone
    resp = await admin_client.get(f"/api/v1/digital-twin/scenarios/{scenario_id}")
    assert resp.status_code == 404


async def test_delete_running_scenario_blocked(fleet_ids, admin_client, session):
    """Deleting a scenario with status 'running' must be blocked (409)."""
    from backend.db.models.scenario import SimulationRun

    await admin_client.post(
        "/api/v1/digital-twin/assignments",
        json={
            "assignment_id": "del-run-a-1",
            "driver_id": fleet_ids["driver"],
            "vehicle_id": fleet_ids["vehicle"],
            "route_id": fleet_ids["route"],
        },
    )
    resp = await admin_client.post(
        "/api/v1/digital-twin/scenarios?assignment_ids=del-run-a-1",
        json={"name": "Running Scenario", "seed": 1},
    )
    scenario_id = resp.json()["data"]["scenario_id"]

    # Force status to 'running' via direct DB update
    from sqlalchemy import update as sa_update

    from backend.db.models.scenario import SimulationScenario

    await session.execute(
        sa_update(SimulationScenario)
        .where(SimulationScenario.scenario_id == scenario_id)
        .values(status="running")
    )
    await session.flush()

    # Insert a run (representing the active execution)
    run = SimulationRun(
        scenario_id=scenario_id,
        status="running",
        seed=42,
    )
    session.add(run)
    await session.flush()
    await session.commit()

    # Delete is blocked
    resp = await admin_client.delete(
        f"/api/v1/digital-twin/scenarios/{scenario_id}"
    )
    assert resp.status_code == 409, resp.text

    # Scenario still exists
    resp = await admin_client.get(f"/api/v1/digital-twin/scenarios/{scenario_id}")
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Scenario creation: comma-separated assignment_ids query contract
# ---------------------------------------------------------------------------


async def _make_assignments(admin_client, prefix: str) -> list[str]:
    """Create 3 drivers/vehicles/routes and 3 assignments with unique
    triples; returns the assignment ids."""
    ids = []
    for i in (1, 2, 3):
        driver_id = f"{prefix}-d{i}"
        vehicle_id = f"{prefix}-v{i}"
        route_id = f"{prefix}-r{i}"
        assignment_id = f"{prefix}-a{i}"

        resp = await admin_client.post(
            "/api/v1/digital-twin/drivers",
            json={
                "driver_id": driver_id,
                "first_name": f"FN{i}",
                "last_name": f"LN{i}",
                "license_number": f"{prefix.upper()}-LIC-{i}",
            },
        )
        assert resp.status_code == 200, resp.text

        resp = await admin_client.post(
            "/api/v1/digital-twin/vehicles",
            json={
                "vehicle_id": vehicle_id,
                "registration_number": f"{prefix.upper()}-REG-{i}",
                "vin": f"{prefix.upper()}VIN0000000{i}",
                "manufacturer": "Test",
                "model": "Model",
                "year": 2024,
            },
        )
        assert resp.status_code == 200, resp.text

        resp = await admin_client.post(
            "/api/v1/digital-twin/routes",
            json={
                "route_id": route_id,
                "name": f"Route {i}",
                "route_type": "urban",
                "origin": "O",
                "destination": f"D{i}",
                "estimated_distance_km": 5.0,
                "speed_limit_kmh": 60.0,
            },
        )
        assert resp.status_code == 200, resp.text

        resp = await admin_client.post(
            "/api/v1/digital-twin/assignments",
            json={
                "assignment_id": assignment_id,
                "driver_id": driver_id,
                "vehicle_id": vehicle_id,
                "route_id": route_id,
            },
        )
        assert resp.status_code == 200, resp.text
        ids.append(assignment_id)
    return ids


async def _scenario_assignment_rows(session, scenario_id: str):
    from backend.db.models.scenario import scenario_assignments

    result = await session.execute(
        select(scenario_assignments.c.assignment_id).where(
            scenario_assignments.c.scenario_id == scenario_id
        )
    )
    return list(result.scalars())


async def test_create_scenario_with_comma_separated_assignment_ids(
    admin_client, session
):
    """POST /digital-twin/scenarios?assignment_ids=A01,A02,A03 must accept
    the comma-separated form produced by the Digital Twin Lab UI and persist
    every assignment."""
    ids = await _make_assignments(admin_client, prefix="csa")

    resp = await admin_client.post(
        "/api/v1/digital-twin/scenarios?assignment_ids=" + ",".join(ids),
        json={"name": "Comma Scenario", "seed": 7},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    scenario_id = data["scenario_id"]
    assert data["name"] == "Comma Scenario"
    assert sorted(data["assignment_ids"]) == sorted(ids)

    # scenario_assignments association rows exist exactly once per id
    assert sorted(await _scenario_assignment_rows(session, scenario_id)) == sorted(ids)

    # GET individual scenario serializes the persisted ids
    resp = await admin_client.get(
        f"/api/v1/digital-twin/scenarios/{scenario_id}"
    )
    assert resp.status_code == 200
    assert sorted(resp.json()["data"]["assignment_ids"]) == sorted(ids)

    # GET list serializes the persisted ids
    resp = await admin_client.get("/api/v1/digital-twin/scenarios")
    listed = next(
        s for s in resp.json()["data"] if s["scenario_id"] == scenario_id
    )
    assert sorted(listed["assignment_ids"]) == sorted(ids)


async def test_create_scenario_with_repeated_assignment_ids(admin_client):
    """The repeated-parameter form (?a=1&a=2) must keep working."""
    ids = await _make_assignments(admin_client, prefix="rep")

    url = (
        "/api/v1/digital-twin/scenarios?"
        + "&".join(f"assignment_ids={aid}" for aid in ids)
    )
    resp = await admin_client.post(url, json={"name": "Repeated Scenario"})
    assert resp.status_code == 200, resp.text
    assert sorted(resp.json()["data"]["assignment_ids"]) == sorted(ids)


async def test_create_scenario_invalid_assignment_id_creates_nothing(
    admin_client, session
):
    """A nonexistent assignment id in the comma list must 404 and must not
    leave a partial scenario or partial scenario_assignments rows behind."""
    ids = await _make_assignments(admin_client, prefix="inv")
    before = await _scenario_assignment_rows(session, "__never__")

    resp = await admin_client.post(
        "/api/v1/digital-twin/scenarios?assignment_ids="
        + ",".join(ids)
        + ",does-not-exist-99",
        json={"name": "Invalid Scenario"},
    )
    assert resp.status_code == 404, resp.text
    assert "does-not-exist-99" in resp.json()["detail"]

    # No partial scenario leaked into the list
    resp = await admin_client.get("/api/v1/digital-twin/scenarios")
    names = [s["name"] for s in resp.json()["data"]]
    assert "Invalid Scenario" not in names

    # scenario_assignments has no partial rows for any of the supplied ids
    from backend.db.models.scenario import scenario_assignments

    result = await session.execute(
        select(scenario_assignments.c.scenario_id)
        .where(scenario_assignments.c.assignment_id.in_(ids + ["does-not-exist-99"]))
    )
    assert list(result.scalars()) == []


async def test_create_scenario_single_assignment_keeps_working(fleet_ids, admin_client):
    """The single-value form used by the lifecycle tests still works."""
    resp = await admin_client.post(
        "/api/v1/digital-twin/assignments",
        json={
            "assignment_id": "single-a-1",
            "driver_id": fleet_ids["driver"],
            "vehicle_id": fleet_ids["vehicle"],
            "route_id": fleet_ids["route"],
        },
    )
    assert resp.status_code == 200, resp.text

    resp = await admin_client.post(
        "/api/v1/digital-twin/scenarios?assignment_ids=single-a-1",
        json={"name": "Single Assignment Scenario"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["assignment_ids"] == ["single-a-1"]
