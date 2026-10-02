"""M5.2 Authorization Perimeter Regression Test.

The mission requirement is not "everything must require admin" — it is:

    every mutation must have an intentional authorization policy, and
    every read endpoint must have an intentional exposure policy.

This module makes both statements executable. It drives the real
application through the anonymous ``client`` fixture and asserts the
inventory: the OpenAPI schema is the source of the route inventory, and
every route must be classified by a declared policy. A new route cannot
ship without declaring who may read or mutate it.

Policy model
------------
PUBLIC_MUTATIONS
    Credential exchange a client must reach before it holds a token
    (signup/login). Anonymous callers must not be rejected here.
ANONYMOUS_READS
    Deliberately public read-only fleet data (dashboard/vehicles/trips/
    telemetry/alerts/health). Anonymous callers must receive 200.
ADMIN_ONLY_READS
    Control-plane reads (Digital Twin, Settings, /auth/me). Anonymous
    callers must receive 401/403.
MUTATIONS (everything else)
    Must reject anonymous callers with 401/403.
"""

import re

import pytest
from httpx import AsyncClient

from backend.api.main import app

# Path template placeholders are filled with a value that cannot exist, so
# an unguarded mutation surfaces as 404 instead of silently "succeeding".
_DUMMY = "00000000-0000-0000-0000-000000000000"
_PARAM = re.compile(r"\{[^}]+\}")

MUTATING = {"post", "put", "patch", "delete"}

# Credential exchange — must stay reachable without a session.
PUBLIC_MUTATIONS = {
    ("/api/v1/auth/signup", "post"),
    ("/api/v1/auth/login", "post"),
}

# Deliberately anonymous read-only fleet telemetry/dashboard/analytics
# surface. These expose operational data only — never configuration.
ANONYMOUS_READS = {
    "/",
    "/api/v1/vehicles",
    "/api/v1/vehicles/{vehicle_id}",
    "/api/v1/drivers",
    "/api/v1/drivers/{driver_id}",
    "/api/v1/routes",
    "/api/v1/routes/{route_id}",
    "/api/v1/trips",
    "/api/v1/trips/{trip_id}",
    "/api/v1/telemetry",
    "/api/v1/telemetry/{vehicle_id}",
    "/api/v1/vehicle-health",
    "/api/v1/vehicle-health/{vehicle_id}",
    "/api/v1/vehicle-health/config",
    "/api/v1/driver-statistics",
    "/api/v1/driver-statistics/{driver_id}",
    "/api/v1/maintenance",
    "/api/v1/maintenance/{vehicle_id}",
    "/api/v1/alerts",
    "/api/v1/alerts/stats",
    "/api/v1/alerts/{vehicle_id}",
    "/api/v1/analytics/summary",
    "/api/v1/analytics/vehicles",
    "/api/v1/analytics/drivers",
    "/api/v1/analytics/drivers/{driver_id}/trend",
    "/api/v1/analytics/trips",
    "/api/v1/analytics/events",
    "/api/v1/analytics/events/trend",
    "/api/v1/analytics/fleet-trend",
    "/api/v1/analytics/insights",
    "/api/v1/analytics/safety-distribution",
    "/api/v1/system/health",
    "/api/v1/system/version",
    "/api/v1/system/status",
}

# Control-plane reads: admin-only by design (fleet configuration, settings).
# Only paths that actually expose a GET are listed — the Digital Twin
# detail paths (drivers/vehicles/routes/assignments by id) are
# PATCH/DELETE only and therefore have no read exposure to classify.
ADMIN_ONLY_READS = {
    "/api/v1/digital-twin/status",
    "/api/v1/digital-twin/drivers",
    "/api/v1/digital-twin/vehicles",
    "/api/v1/digital-twin/routes",
    "/api/v1/digital-twin/assignments",
    "/api/v1/digital-twin/scenarios",
    "/api/v1/digital-twin/scenarios/{scenario_id}",
    "/api/v1/digital-twin/scenarios/{scenario_id}/runs",
    "/api/v1/settings",
    "/api/v1/settings/{category}",
    "/api/v1/auth/me",
}


def _schema_paths() -> dict[str, set[str]]:
    schema = app.openapi()
    return {path: set(methods) for path, methods in schema["paths"].items()}


def _expand(path: str) -> str:
    return _PARAM.sub(_DUMMY, path)


def _mutations() -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for path, methods in _schema_paths().items():
        for method in sorted(methods & MUTATING):
            out.append((path, method))
    return sorted(out)


def _reads() -> list[str]:
    return sorted(p for p, m in _schema_paths().items() if "get" in m)


MUTATIONS = _mutations()
READS = _reads()


class TestInventoryIsClassified:
    """Every route must be explicitly classified — no implicit policy."""

    def test_mutation_inventory_is_not_empty(self) -> None:
        assert MUTATIONS, "expected the application to expose mutations"

    def test_public_mutations_are_credential_exchange_only(self) -> None:
        for path, _method in PUBLIC_MUTATIONS:
            assert path in _schema_paths(), (
                f"policy lists {path}, which is not in the OpenAPI schema"
            )
            assert path.startswith("/api/v1/auth/"), (
                f"{path} is declared public-mutating but is not an auth "
                "endpoint; public mutations must be justified explicitly"
            )

    def test_read_inventory_is_classified(self) -> None:
        classified = ANONYMOUS_READS | ADMIN_ONLY_READS
        unclassified = [p for p in READS if p not in classified]
        assert not unclassified, (
            "undocumented read exposure policy for: "
            f"{unclassified}. Add each to ANONYMOUS_READS (public read-only) "
            "or ADMIN_ONLY_READS (admin control plane)."
        )

    def test_classified_reads_all_exist(self) -> None:
        """No policy entry points at a route that no longer exists."""
        schema_paths = _schema_paths()
        for path in ANONYMOUS_READS | ADMIN_ONLY_READS:
            assert path in schema_paths, (
                f"policy lists {path}, which is not in the OpenAPI schema"
            )


class TestMutationPerimeter:
    """Every mutation except credential exchange rejects anonymous callers."""

    @pytest.mark.parametrize(
        "path,method",
        [pytest.param(p, m, id=f"{m.upper()} {p}") for p, m in MUTATIONS],
    )
    async def test_mutation_rejects_anonymous(
        self,
        client: AsyncClient,
        path: str,
        method: str,
    ) -> None:
        if (path, method) in PUBLIC_MUTATIONS:
            return
        response = await client.request(
            method.upper(),
            _expand(path),
            json={},
        )
        assert response.status_code in (401, 403), (
            f"{method.upper()} {path} accepted an anonymous mutation "
            f"(status {response.status_code})"
        )

    async def test_credential_exchange_stays_public(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@example.invalid", "password": "wrong"},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "INVALID_CREDENTIALS"


class TestReadExposure:
    """Reads keep their declared exposure: public or admin-only."""

    @pytest.mark.parametrize(
        "path",
        [pytest.param(p, id=p) for p in sorted(ANONYMOUS_READS)],
    )
    async def test_anonymous_reads_are_reachable(
        self,
        client: AsyncClient,
        path: str,
    ) -> None:
        response = await client.get(_expand(path))
        assert response.status_code not in (401, 403), (
            f"{path} is declared anonymously readable but returned "
            f"{response.status_code}"
        )
        if "{" not in path and path != "/":
            # Collection reads must actually serve data; detail reads
            # legitimately 404 for the non-existent placeholder id.
            assert response.status_code == 200, (
                f"{path} is declared anonymously readable but returned "
                f"{response.status_code}: {response.text[:200]}"
            )

    async def test_service_root_is_public(self) -> None:
        """The service root is mounted on the full app, not the v1 router."""
        from httpx import ASGITransport, AsyncClient as RootClient

        transport = ASGITransport(app=app)
        async with RootClient(transport=transport, base_url="http://test") as root:
            response = await root.get("/")

        assert response.status_code == 200
        assert response.json()["name"] == "DriveVitals"

    @pytest.mark.parametrize(
        "path",
        [pytest.param(p, id=p) for p in sorted(ADMIN_ONLY_READS)],
    )
    async def test_admin_only_reads_reject_anonymous(
        self,
        client: AsyncClient,
        path: str,
    ) -> None:
        response = await client.get(_expand(path))
        assert response.status_code in (401, 403), (
            f"{path} is declared admin-only but returned "
            f"{response.status_code}"
        )

    async def test_admin_only_reads_reject_operator(
        self,
        operator_client: AsyncClient,
    ) -> None:
        response = await operator_client.get("/api/v1/digital-twin/scenarios")
        assert response.status_code == 403

    async def test_admin_only_reads_allow_admin(self, admin_client: AsyncClient) -> None:
        response = await admin_client.get("/api/v1/digital-twin/scenarios")
        assert response.status_code == 200


class TestWebSocketAuthentication:
    """WebSocket channels authenticate with a session token (4401)."""

    @pytest.mark.parametrize(
        "channel",
        [pytest.param("dashboard", id="dashboard"),
         pytest.param("trips", id="trips"),
         pytest.param("alerts", id="alerts")],
    )
    def test_channel_module_authenticates(self, channel: str) -> None:
        import importlib

        module = importlib.import_module(f"backend.api.websocket.{channel}")
        source_path = module.__file__
        assert source_path is not None
        with open(source_path, "r", encoding="utf-8") as handle:
            source = handle.read()
        assert "authenticate_ws" in source, (
            f"ws/{channel} must authenticate via authenticate_ws"
        )
        assert "WS_AUTH_REJECT_CODE" in source, (
            f"ws/{channel} must reject unauthenticated clients with 4401"
        )

