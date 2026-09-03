"""API tests for the Digital Twin Lab (admin-only).

Verifies authorization guards and the managed CRUD + scenario lifecycle
surface. Launch/stop/reset require a wired simulation controller, which
the API test harness does not provide; those return 503 here and are
exercised directly against the controller in the integration suite.
"""

import pytest

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

    # activate requires at least one assignment; it has one -> ready
    resp = await admin_client.post(
        f"/api/v1/digital-twin/scenarios/{scenario_id}/activate"
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["status"] == "ready"

    # cannot edit a scenario with invalid status
    resp = await admin_client.patch(
        f"/api/v1/digital-twin/scenarios/{scenario_id}",
        json={"status": "bogus"},
    )
    assert resp.status_code == 422

    # list scenarios
    resp = await admin_client.get("/api/v1/digital-twin/scenarios")
    assert resp.status_code == 200
    names = [s["name"] for s in resp.json()["data"]]
    assert "Test Scenario" in names

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
