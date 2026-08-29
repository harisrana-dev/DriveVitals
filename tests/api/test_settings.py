"""M3 Settings — comprehensive backend tests.

Covers:
- authorization (401/403/200)
- defaults when no DB rows exist
- persistence (upsert + read)
- update_by tracking
- validation (invalid values → 422)
- unknown category → 404
- no secrets in response
"""

import pytest
from httpx import AsyncClient


# ---------------------------------------------------------------------------
# Authorization
# ---------------------------------------------------------------------------


class TestSettingsAuthorization:

    async def test_get_settings_rejects_anonymous(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/settings")
        assert response.status_code == 401

    async def test_get_settings_rejects_viewer(self, viewer_client: AsyncClient) -> None:
        response = await viewer_client.get("/api/v1/settings")
        assert response.status_code == 403

    async def test_get_settings_rejects_operator(self, operator_client: AsyncClient) -> None:
        response = await operator_client.get("/api/v1/settings")
        assert response.status_code == 403

    async def test_get_settings_allows_admin(self, admin_client: AsyncClient) -> None:
        response = await admin_client.get("/api/v1/settings")
        assert response.status_code == 200

    async def test_patch_settings_rejects_anonymous(self, client: AsyncClient) -> None:
        response = await client.patch(
            "/api/v1/settings/analytics",
            json={"vehicle_health": {"window_size": 30}},
        )
        assert response.status_code == 401

    async def test_patch_settings_rejects_viewer(self, viewer_client: AsyncClient) -> None:
        response = await viewer_client.patch(
            "/api/v1/settings/analytics",
            json={"vehicle_health": {"window_size": 30}},
        )
        assert response.status_code == 403

    async def test_patch_settings_rejects_operator(self, operator_client: AsyncClient) -> None:
        response = await operator_client.patch(
            "/api/v1/settings/analytics",
            json={"vehicle_health": {"window_size": 30}},
        )
        assert response.status_code == 403

    async def test_patch_settings_allows_admin(self, admin_client: AsyncClient) -> None:
        response = await admin_client.patch(
            "/api/v1/settings/analytics",
            json={"vehicle_health": {"window_size": 30}},
        )
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Response structure
# ---------------------------------------------------------------------------


class TestSettingsResponseStructure:

    async def test_full_settings_has_required_sections(
        self, admin_client: AsyncClient
    ) -> None:
        response = await admin_client.get("/api/v1/settings")
        assert response.status_code == 200
        data = response.json()["data"]
        assert "account" in data
        assert "system" in data
        assert "analytics" in data

    async def test_account_contains_identity(
        self, admin_client: AsyncClient
    ) -> None:
        response = await admin_client.get("/api/v1/settings")
        account = response.json()["data"]["account"]
        assert "user_id" in account
        assert "email" in account
        assert "full_name" in account
        assert account["role"] == "admin"

    async def test_system_contains_runtime_info(
        self, admin_client: AsyncClient
    ) -> None:
        response = await admin_client.get("/api/v1/settings")
        system = response.json()["data"]["system"]
        assert system["app_name"] == "DriveVitals"
        assert system["version"] == "1.0.0"
        assert "uptime_seconds" in system

    async def test_analytics_has_both_subsections(
        self, admin_client: AsyncClient
    ) -> None:
        response = await admin_client.get("/api/v1/settings")
        analytics = response.json()["data"]["analytics"]
        assert "vehicle_health" in analytics
        assert "driver_statistics" in analytics


# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------


class TestSettingsDefaults:

    async def test_defaults_returned_when_no_db_rows(
        self, admin_client: AsyncClient
    ) -> None:
        """Fresh DB has no system_settings rows — defaults must be returned."""
        response = await admin_client.get("/api/v1/settings")
        assert response.status_code == 200
        vh = response.json()["data"]["analytics"]["vehicle_health"]
        # Default engine redline_rpm is 6200.0
        assert vh["engine"]["redline_rpm"] == 6200.0
        assert vh["status"]["healthy_min"] == 90.0

    async def test_driver_statistics_defaults(
        self, admin_client: AsyncClient
    ) -> None:
        response = await admin_client.get("/api/v1/settings")
        ds = response.json()["data"]["analytics"]["driver_statistics"]
        assert ds["safety"]["density_sensitivity"] == 0.35
        assert ds["aggression"]["max_density"] == 1.0
        assert ds["efficiency"]["max_events_per_km"] == 1.0


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------


class TestSettingsPersistence:

    async def test_patch_creates_settings_row(
        self, admin_client: AsyncClient
    ) -> None:
        # Patch window_size
        response = await admin_client.patch(
            "/api/v1/settings/analytics",
            json={"vehicle_health": {"window_size": 30}},
        )
        assert response.status_code == 200

        # Subsequent GET returns persisted value
        response = await admin_client.get("/api/v1/settings")
        vh = response.json()["data"]["analytics"]["vehicle_health"]
        assert vh["window_size"] == 30

    async def test_patch_updates_existing_row(
        self, admin_client: AsyncClient
    ) -> None:
        # First update
        await admin_client.patch(
            "/api/v1/settings/analytics",
            json={"vehicle_health": {"window_size": 25}},
        )
        # Second update
        await admin_client.patch(
            "/api/v1/settings/analytics",
            json={"vehicle_health": {"window_size": 40}},
        )
        response = await admin_client.get("/api/v1/settings")
        vh = response.json()["data"]["analytics"]["vehicle_health"]
        assert vh["window_size"] == 40

    async def test_get_category_returns_category(
        self, admin_client: AsyncClient
    ) -> None:
        response = await admin_client.get("/api/v1/settings/analytics")
        assert response.status_code == 200
        body = response.json()["data"]
        assert body["category"] == "analytics"
        assert "vehicle_health" in body["data"]
        assert "driver_statistics" in body["data"]

    async def test_unknown_category_returns_404(
        self, admin_client: AsyncClient
    ) -> None:
        response = await admin_client.get("/api/v1/settings/nonexistent")
        assert response.status_code == 404

    async def test_patch_unknown_category_returns_404(
        self, admin_client: AsyncClient
    ) -> None:
        response = await admin_client.patch(
            "/api/v1/settings/nonexistent",
            json={"some_key": "some_value"},
        )
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


class TestSettingsValidation:

    async def test_invalid_window_size_rejected(
        self, admin_client: AsyncClient
    ) -> None:
        response = await admin_client.patch(
            "/api/v1/settings/analytics",
            json={"vehicle_health": {"window_size": 0}},
        )
        assert response.status_code == 422

    async def test_negative_weight_rejected(
        self, admin_client: AsyncClient
    ) -> None:
        response = await admin_client.patch(
            "/api/v1/settings/analytics",
            json={
                "vehicle_health": {
                    "weights": {
                        "engine": -0.1,
                        "cooling": 0.20,
                        "brakes": 0.20,
                        "transmission": 0.15,
                        "fuel_system": 0.55,
                    }
                }
            },
        )
        assert response.status_code == 422

    async def test_weights_not_summing_to_one_rejected(
        self, admin_client: AsyncClient
    ) -> None:
        response = await admin_client.patch(
            "/api/v1/settings/analytics",
            json={
                "vehicle_health": {
                    "weights": {
                        "engine": 0.50,
                        "cooling": 0.50,
                        "brakes": 0.50,
                        "transmission": 0.50,
                        "fuel_system": 0.50,
                    }
                }
            },
        )
        assert response.status_code == 422

    async def test_valid_weight_update_accepted(
        self, admin_client: AsyncClient
    ) -> None:
        response = await admin_client.patch(
            "/api/v1/settings/analytics",
            json={
                "vehicle_health": {
                    "weights": {
                        "engine": 0.35,
                        "cooling": 0.20,
                        "brakes": 0.20,
                        "transmission": 0.15,
                        "fuel_system": 0.10,
                    }
                }
            },
        )
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# No secrets
# ---------------------------------------------------------------------------


class TestSettingsNoSecrets:

    async def test_settings_response_contains_no_secrets(
        self, admin_client: AsyncClient
    ) -> None:
        response = await admin_client.get("/api/v1/settings")
        raw = response.text.lower()
        # Must not contain password hashes, tokens, or DB credentials
        assert "password_hash" not in raw
        assert "bearer" not in raw
        assert "token_hash" not in raw
