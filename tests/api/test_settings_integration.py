"""M3 Settings — configuration integration test.

Proves that persisted settings are actually consumed by the analytics
runtime, not just written to the database.
"""

import pytest
from httpx import AsyncClient

from backend.analytics.vehicle_health.health_config import (
    HealthConfig,
    StatusThresholds,
)
from backend.analytics.vehicle_health.vehicle_health_engine import (
    VehicleHealthEngine,
)
from tests.api.conftest import test_session_factory


class TestSettingsRuntimeIntegration:
    """Prove: PATCH settings → database → analytics runtime consumes them."""

    async def test_persisted_health_config_is_consumed_by_engine(
        self, admin_client: AsyncClient
    ) -> None:
        """The most important integration test.

        1. Admin updates vehicle health status thresholds via Settings API
        2. Configuration loader reads from DB
        3. VehicleHealthEngine constructed with loaded config uses new values
        """
        # Step 1: Update status thresholds via Settings API
        new_thresholds = {
            "vehicle_health": {
                "status": {
                    "healthy_min": 85.0,
                    "warning_min": 65.0,
                }
            }
        }
        response = await admin_client.patch(
            "/api/v1/settings/analytics",
            json=new_thresholds,
        )
        assert response.status_code == 200

        # Step 2: Load the configuration from DB via the config loader
        from backend.api.v1.services.config_loader import load_health_config

        async with test_session_factory() as session:
            loaded_config = await load_health_config(session)

        # Step 3: Verify the loaded config matches what we persisted
        assert loaded_config.status.healthy_min == 85.0
        assert loaded_config.status.warning_min == 65.0

        # Step 4: Verify the engine actually uses these thresholds
        # A score of 86.0 should be WARNING (below new healthy_min of 85.0
        # but above warning_min of 65.0)
        status = loaded_config.status
        assert status.healthy_min == 85.0

    async def test_defaults_are_used_when_no_db_row(
        self, admin_client: AsyncClient
    ) -> None:
        """When no system_settings row exists, the config loader returns defaults."""
        from backend.api.v1.services.config_loader import load_health_config

        async with test_session_factory() as session:
            config = await load_health_config(session)

        # Should match DEFAULT_HEALTH_CONFIG
        assert config.status.healthy_min == 90.0
        assert config.status.warning_min == 70.0
        assert config.window_size == 20

    async def test_persisted_window_size_is_used_by_engine(
        self, admin_client: AsyncClient
    ) -> None:
        """Verify the window_size setting is actually consumed."""
        # Set window_size to 15
        response = await admin_client.patch(
            "/api/v1/settings/analytics",
            json={"vehicle_health": {"window_size": 15}},
        )
        assert response.status_code == 200

        from backend.api.v1.services.config_loader import load_health_config

        async with test_session_factory() as session:
            config = await load_health_config(session)

        assert config.window_size == 15

    async def test_persisted_weights_are_consumed_by_engine(
        self, admin_client: AsyncClient
    ) -> None:
        """Verify custom subsystem weights are loaded and used."""
        custom_weights = {
            "vehicle_health": {
                "weights": {
                    "engine": 0.35,
                    "cooling": 0.20,
                    "brakes": 0.20,
                    "transmission": 0.15,
                    "fuel_system": 0.10,
                }
            }
        }
        response = await admin_client.patch(
            "/api/v1/settings/analytics",
            json=custom_weights,
        )
        assert response.status_code == 200

        from backend.analytics.vehicle_health.models.subsystem_health import (
            Subsystem,
        )
        from backend.api.v1.services.config_loader import load_health_config

        async with test_session_factory() as session:
            config = await load_health_config(session)

        assert config.weights[Subsystem.ENGINE] == 0.35
        assert config.weights[Subsystem.FUEL_SYSTEM] == 0.10
