from httpx import AsyncClient


class TestVehicleHealth:

    async def test_list_vehicle_health(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/vehicle-health")

        assert response.status_code == 200
        payload = response.json()
        assert payload["count"] == 1
        assert payload["data"][0]["vehicle_id"] == "v-1"

    async def test_list_vehicle_health_pagination(self, client: AsyncClient) -> None:
        response = await client.get(
            "/api/v1/vehicle-health", params={"limit": 5, "offset": 0}
        )

        assert response.status_code == 200
        assert len(response.json()["data"]) == 1

    async def test_get_vehicle_health(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/vehicle-health/v-1")

        assert response.status_code == 200
        record = response.json()["data"]
        assert record["vehicle_id"] == "v-1"
        assert record["overall_health_score"] == 88.5
        assert record["engine_health"] == 90.0
        assert record["fuel_system_health"] == 80.0

    async def test_get_vehicle_health_not_found(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/vehicle-health/v-99")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
