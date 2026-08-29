import pytest
from httpx import AsyncClient

MUTATIONS = [
    ("DELETE", "/api/v1/trips/aborted", None),
    ("DELETE", "/api/v1/trips/t-5", None),
    ("POST", "/api/v1/alerts/a-1/acknowledge", None),
    ("POST", "/api/v1/alerts/a-1/resolve", None),
]


class TestMutationAuthorization:

    @pytest.mark.parametrize("method,path,body", MUTATIONS)
    async def test_mutations_reject_anonymous(
        self,
        client: AsyncClient,
        method: str,
        path: str,
        body,
    ) -> None:
        response = await client.request(method, path, json=body)
        assert response.status_code == 401

    @pytest.mark.parametrize("method,path,body", MUTATIONS)
    async def test_mutations_reject_viewer(
        self,
        viewer_client: AsyncClient,
        method: str,
        path: str,
        body,
    ) -> None:
        response = await viewer_client.request(method, path, json=body)
        assert response.status_code == 403

    @pytest.mark.parametrize("method,path,body", MUTATIONS)
    async def test_mutations_accepted_for_operator(
        self,
        operator_client: AsyncClient,
        method: str,
        path: str,
        body,
    ) -> None:
        response = await operator_client.request(method, path, json=body)
        assert response.status_code in (200, 204)


class TestMaintenanceAuthorization:

    async def _complete(self, client: AsyncClient) -> int:
        mid = (
            await client.get("/api/v1/maintenance", params={"limit": 1})
        ).json()["data"][0]["maintenance_id"]
        response = await client.patch(
            f"/api/v1/maintenance/{mid}/complete",
            json={"completed_odometer_km": 99999.0},
        )
        return response.status_code

    async def test_maintenance_complete_rejects_anonymous(
        self, client: AsyncClient
    ) -> None:
        assert await self._complete(client) == 401

    async def test_maintenance_complete_rejects_viewer(
        self, viewer_client: AsyncClient
    ) -> None:
        assert await self._complete(viewer_client) == 403

    async def test_maintenance_complete_allows_operator(
        self, operator_client: AsyncClient
    ) -> None:
        assert await self._complete(operator_client) == 200

    async def test_maintenance_complete_allows_admin(
        self, admin_client: AsyncClient
    ) -> None:
        assert await self._complete(admin_client) == 200


class TestSettingsAuthorization:

    async def test_settings_rejects_anonymous(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/settings")
        assert response.status_code == 401

    async def test_settings_rejects_viewer(
        self, viewer_client: AsyncClient
    ) -> None:
        response = await viewer_client.get("/api/v1/settings")
        assert response.status_code == 403

    async def test_settings_rejects_operator(
        self, operator_client: AsyncClient
    ) -> None:
        response = await operator_client.get("/api/v1/settings")
        assert response.status_code == 403

    async def test_settings_allows_admin(
        self, admin_client: AsyncClient
    ) -> None:
        response = await admin_client.get("/api/v1/settings")
        assert response.status_code == 200
        body = response.json()
        assert body["data"] == {"settings": {}}


class TestReadOnlyStaysAnonymous:

    READ_ENDPOINTS = [
        "/api/v1/vehicles",
        "/api/v1/vehicles/v-1",
        "/api/v1/drivers",
        "/api/v1/routes",
        "/api/v1/trips",
        "/api/v1/alerts",
        "/api/v1/maintenance",
        "/api/v1/telemetry?latest=true",
        "/api/v1/vehicle-health",
        "/api/v1/system/health",
    ]

    @pytest.mark.parametrize("path", READ_ENDPOINTS)
    async def test_read_endpoints_do_not_require_auth(
        self, client: AsyncClient, path: str
    ) -> None:
        response = await client.get(path)
        assert response.status_code == 200


class TestForbiddenIsNeverUnauthorized:

    """Regression: a role mismatch must yield 403, never 401."""

    async def test_viewer_role_mismatch_returns_403(
        self, viewer_client: AsyncClient
    ) -> None:
        response = await viewer_client.delete("/api/v1/trips/t-5")
        assert response.status_code == 403
        assert response.json()["detail"] == "INSUFFICIENT_PERMISSIONS"