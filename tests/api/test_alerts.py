from httpx import AsyncClient


class TestAlerts:

    async def test_list_alerts(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/alerts")

        assert response.status_code == 200
        payload = response.json()
        assert payload["count"] == 3
        assert len(payload["data"]) == 3

    async def test_list_alerts_by_vehicle(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/alerts/v-1")

        assert response.status_code == 200
        payload = response.json()
        assert payload["count"] == 3
        assert all(item["vehicle_id"] == "v-1" for item in payload["data"])

    async def test_list_alerts_filter_by_severity(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/alerts", params={"severity": "critical"})

        assert response.status_code == 200
        payload = response.json()
        assert payload["count"] == 1
        assert payload["data"][0]["alert_id"] == "a-1"

    async def test_list_alerts_filter_by_type(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/alerts", params={"type": "maintenance"})

        assert response.status_code == 200
        payload = response.json()
        assert payload["count"] == 1
        assert payload["data"][0]["alert_id"] == "a-2"

    async def test_list_alerts_filter_by_acknowledged(
        self, client: AsyncClient
    ) -> None:
        unacknowledged = await client.get(
            "/api/v1/alerts", params={"acknowledged": "false"}
        )
        assert unacknowledged.status_code == 200
        assert unacknowledged.json()["count"] == 1
        assert unacknowledged.json()["data"][0]["alert_id"] == "a-1"

        acknowledged = await client.get(
            "/api/v1/alerts", params={"acknowledged": "true"}
        )
        assert acknowledged.status_code == 200
        assert acknowledged.json()["count"] == 2

    async def test_list_alerts_combined_filters(self, client: AsyncClient) -> None:
        response = await client.get(
            "/api/v1/alerts",
            params={"vehicle_id": "v-1", "acknowledged": "true"},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["count"] == 2

    async def test_list_alerts_unknown_vehicle(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/alerts/v-99")

        assert response.status_code == 200
        assert response.json() == {"data": [], "count": 0}

    async def test_list_alerts_pagination(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/alerts", params={"limit": 2})

        assert response.status_code == 200
        payload = response.json()
        assert len(payload["data"]) == 2
        assert payload["count"] == 3

    async def test_list_alerts_invalid_pagination(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/alerts", params={"offset": -1})

        assert response.status_code == 400
