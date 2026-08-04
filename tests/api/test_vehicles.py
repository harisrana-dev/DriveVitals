from httpx import AsyncClient


class TestVehicles:

    async def test_list_vehicles(self, client: AsyncClient, ids: dict[str, str]) -> None:
        response = await client.get("/api/v1/vehicles")

        assert response.status_code == 200
        payload = response.json()
        assert payload["count"] == 5
        assert len(payload["data"]) == 5
        assert {item["vehicle_id"] for item in payload["data"]} == {
            "v-1",
            "v-2",
            "v-3",
            "v-4",
            "v-5",
        }

    async def test_list_vehicles_filter_by_status(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/vehicles", params={"status": "maintenance"})

        assert response.status_code == 200
        payload = response.json()
        assert payload["count"] == 1
        assert payload["data"][0]["vehicle_id"] == "v-5"

    async def test_list_vehicles_filter_by_driver(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/vehicles", params={"driver": "d-1"})

        assert response.status_code == 200
        payload = response.json()
        assert payload["count"] == 2
        assert {item["vehicle_id"] for item in payload["data"]} == {"v-1", "v-2"}

    async def test_list_vehicles_filter_by_unknown_driver(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/vehicles", params={"driver": "d-unknown"})

        assert response.status_code == 200
        assert response.json() == {"data": [], "count": 0}

    async def test_list_vehicles_pagination(self, client: AsyncClient) -> None:
        first = await client.get("/api/v1/vehicles", params={"limit": 2})
        assert first.status_code == 200
        assert len(first.json()["data"]) == 2
        assert first.json()["count"] == 5

        second = await client.get(
            "/api/v1/vehicles", params={"limit": 2, "offset": 2}
        )
        assert second.status_code == 200
        first_ids = {item["vehicle_id"] for item in first.json()["data"]}
        second_ids = {item["vehicle_id"] for item in second.json()["data"]}
        assert first_ids.isdisjoint(second_ids)

    async def test_list_vehicles_invalid_pagination(self, client: AsyncClient) -> None:
        for params in ({"limit": 0}, {"limit": 1000}, {"offset": -1}):
            response = await client.get("/api/v1/vehicles", params=params)
            assert response.status_code == 400

    async def test_get_vehicle(self, client: AsyncClient, ids: dict[str, str]) -> None:
        response = await client.get(f"/api/v1/vehicles/{ids['vehicle1']}")

        assert response.status_code == 200
        vehicle = response.json()["data"]
        assert vehicle["vehicle_id"] == "v-1"
        assert vehicle["manufacturer"] == "Test"
        assert vehicle["model"] == "Transit"
        assert vehicle["status"] == "active"

    async def test_get_vehicle_not_found(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/vehicles/does-not-exist")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
