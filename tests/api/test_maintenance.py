from httpx import AsyncClient


class TestMaintenance:

    async def test_list_maintenance(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/maintenance")

        assert response.status_code == 200
        payload = response.json()
        assert payload["count"] == 2
        assert len(payload["data"]) == 2

    async def test_list_maintenance_by_vehicle(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/maintenance/v-1")

        assert response.status_code == 200
        payload = response.json()
        assert payload["count"] == 2
        assert all(item["vehicle_id"] == "v-1" for item in payload["data"])

    async def test_list_maintenance_filter_by_priority(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/maintenance", params={"priority": "high"})

        assert response.status_code == 200
        payload = response.json()
        assert payload["count"] == 1
        assert payload["data"][0]["maintenance_type"] == "engine"

    async def test_list_maintenance_filter_by_component(self, client: AsyncClient) -> None:
        response = await client.get(
            "/api/v1/maintenance", params={"component": "brakes"}
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["count"] == 1
        assert payload["data"][0]["priority"] == "medium"

    async def test_list_maintenance_filtered_vehicle(
        self, client: AsyncClient
    ) -> None:
        response = await client.get(
            "/api/v1/maintenance/v-1", params={"priority": "medium"}
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["count"] == 1
        assert payload["data"][0]["maintenance_type"] == "brakes"

    async def test_list_maintenance_unknown_vehicle(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/maintenance/v-99")

        assert response.status_code == 200
        assert response.json() == {"data": [], "count": 0}

    async def test_list_maintenance_pagination(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/maintenance", params={"limit": 1})

        assert response.status_code == 200
        payload = response.json()
        assert len(payload["data"]) == 1
        assert payload["count"] == 2

    async def test_list_maintenance_invalid_pagination(
        self, client: AsyncClient
    ) -> None:
        response = await client.get("/api/v1/maintenance", params={"limit": 0})

        assert response.status_code == 400
