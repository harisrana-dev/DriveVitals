from httpx import AsyncClient


class TestDrivers:

    async def test_list_drivers(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/drivers")

        assert response.status_code == 200
        payload = response.json()
        assert payload["count"] == 3
        assert len(payload["data"]) == 3

    async def test_list_drivers_pagination(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/drivers", params={"limit": 2, "offset": 1})

        assert response.status_code == 200
        payload = response.json()
        assert len(payload["data"]) == 2
        assert payload["count"] == 3
        assert {item["driver_id"] for item in payload["data"]} == {"d-2", "d-3"}

    async def test_list_drivers_invalid_pagination(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/drivers", params={"limit": -5})

        assert response.status_code == 400

    async def test_get_driver(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/drivers/d-1")

        assert response.status_code == 200
        driver = response.json()["data"]
        assert driver["driver_id"] == "d-1"
        assert driver["first_name"] == "Alice"
        assert driver["last_name"] == "Smith"

    async def test_get_driver_not_found(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/drivers/does-not-exist")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
