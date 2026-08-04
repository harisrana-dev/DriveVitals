from datetime import datetime, timezone

from httpx import AsyncClient


def _iso(dt: str) -> datetime:
    return datetime.fromisoformat(dt.replace("Z", "+00:00"))


class TestTelemetry:

    async def test_list_telemetry(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/telemetry")

        assert response.status_code == 200
        payload = response.json()
        assert payload["count"] == 5
        assert len(payload["data"]) == 5

    async def test_list_telemetry_for_vehicle(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/telemetry/v-1")

        assert response.status_code == 200
        payload = response.json()
        assert payload["count"] == 3
        assert all(item["vehicle_id"] == "v-1" for item in payload["data"])

    async def test_list_telemetry_for_unknown_vehicle(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/telemetry/v-99")

        assert response.status_code == 200
        assert response.json() == {"data": [], "count": 0}

    async def test_list_telemetry_latest(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/telemetry", params={"latest": "true"})

        assert response.status_code == 200
        payload = response.json()
        assert payload["count"] == 2
        vehicles = {item["vehicle_id"] for item in payload["data"]}
        assert vehicles == {"v-1", "v-2"}
        by_vehicle = {item["vehicle_id"]: item for item in payload["data"]}
        assert _iso(by_vehicle["v-1"]["timestamp"]) == datetime(
            2026, 1, 1, 9, 0, 0, tzinfo=timezone.utc
        )
        assert by_vehicle["v-2"]["timestamp"].startswith("2026-01-03T08:30:00")

    async def test_list_telemetry_latest_for_vehicle(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/telemetry/v-1", params={"latest": "true"})

        assert response.status_code == 200
        payload = response.json()
        assert payload["count"] == 1
        assert payload["data"][0]["vehicle_id"] == "v-1"
        assert payload["data"][0]["timestamp"].startswith("2026-01-01T09:00:00")

    async def test_list_telemetry_pagination(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/telemetry/v-1", params={"limit": 2})

        assert response.status_code == 200
        payload = response.json()
        assert len(payload["data"]) == 2
        assert payload["count"] == 3

    async def test_list_telemetry_invalid_pagination(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/telemetry", params={"offset": -1})

        assert response.status_code == 400
