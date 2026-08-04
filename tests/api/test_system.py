from httpx import AsyncClient


class TestSystem:

    async def test_health(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/system/health")

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["status"] == "healthy"
        assert data["database"] == "connected"

    async def test_version(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/system/version")

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["name"] == "DriveVitals"
        assert data["version"] == "1.0.0"
        assert data["api_version"] == "v1"

    async def test_status(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/system/status")

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["name"] == "DriveVitals"
        assert data["status"] == "operational"
        assert data["version"] == "1.0.0"
        assert data["api_version"] == "v1"
        assert data["uptime_seconds"] >= 0
