from httpx import AsyncClient


class TestEmptyDatabase:

    async def test_empty_collections(self, empty_client: AsyncClient) -> None:
        empty = {"data": [], "count": 0}

        for path in (
            "/api/v1/vehicles",
            "/api/v1/drivers",
            "/api/v1/routes",
            "/api/v1/trips",
            "/api/v1/telemetry",
            "/api/v1/vehicle-health",
            "/api/v1/driver-statistics",
            "/api/v1/maintenance",
            "/api/v1/alerts",
        ):
            response = await empty_client.get(path)
            assert response.status_code == 200, path
            assert response.json() == empty, path

    async def test_empty_detail_endpoints_return_404(
        self, empty_client: AsyncClient
    ) -> None:
        for path in (
            "/api/v1/vehicles/v-1",
            "/api/v1/drivers/d-1",
            "/api/v1/routes/r-1",
            "/api/v1/trips/t-1",
            "/api/v1/vehicle-health/v-1",
            "/api/v1/driver-statistics/d-1",
        ):
            response = await empty_client.get(path)
            assert response.status_code == 404, path

    async def test_empty_pagination(self, empty_client: AsyncClient) -> None:
        response = await empty_client.get(
            "/api/v1/vehicles", params={"limit": 10, "offset": 0}
        )

        assert response.status_code == 200
        assert response.json() == {"data": [], "count": 0}
