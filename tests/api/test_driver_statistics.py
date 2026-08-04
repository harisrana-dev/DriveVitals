from httpx import AsyncClient


class TestDriverStatistics:

    async def test_list_driver_statistics(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/driver-statistics")

        assert response.status_code == 200
        payload = response.json()
        assert payload["count"] == 1
        assert payload["data"][0]["driver_id"] == "d-1"

    async def test_get_driver_statistics(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/driver-statistics/d-1")

        assert response.status_code == 200
        record = response.json()["data"]
        assert record["driver_id"] == "d-1"
        assert record["total_trips"] == 3
        assert record["safety_score"] == 84.0
        assert record["harsh_braking_events"] == 2

    async def test_get_driver_statistics_not_found(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/driver-statistics/d-99")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
