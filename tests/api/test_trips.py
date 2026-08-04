from httpx import AsyncClient


class TestTrips:

    async def test_list_trips(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/trips")

        assert response.status_code == 200
        payload = response.json()
        assert payload["count"] == 4
        assert len(payload["data"]) == 4

    async def test_list_trips_filter_by_vehicle(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/trips", params={"vehicle_id": "v-1"})

        assert response.status_code == 200
        payload = response.json()
        assert payload["count"] == 2
        assert {item["trip_id"] for item in payload["data"]} == {"t-1", "t-2"}

    async def test_list_trips_filter_by_driver(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/trips", params={"driver_id": "d-1"})

        assert response.status_code == 200
        payload = response.json()
        assert payload["count"] == 2
        assert {item["trip_id"] for item in payload["data"]} == {"t-1", "t-3"}

    async def test_list_trips_filter_by_completed(self, client: AsyncClient) -> None:
        completed = await client.get("/api/v1/trips", params={"completed": "true"})
        assert completed.status_code == 200
        assert completed.json()["count"] == 3
        assert all(
            item["status"] == "completed" for item in completed.json()["data"]
        )

        in_progress = await client.get("/api/v1/trips", params={"completed": "false"})
        assert in_progress.status_code == 200
        assert in_progress.json()["count"] == 1
        assert in_progress.json()["data"][0]["status"] == "in_progress"

    async def test_list_trips_pagination(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/trips", params={"limit": 2, "offset": 2})

        assert response.status_code == 200
        payload = response.json()
        assert len(payload["data"]) == 2
        assert payload["count"] == 4

    async def test_list_trips_invalid_pagination(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/trips", params={"limit": 501})

        assert response.status_code == 400

    async def test_get_trip(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/trips/t-1")

        assert response.status_code == 200
        trip = response.json()["data"]
        assert trip["trip_id"] == "t-1"
        assert trip["vehicle_id"] == "v-1"
        assert trip["driver_id"] == "d-1"
        assert trip["status"] == "completed"

    async def test_get_trip_not_found(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/trips/does-not-exist")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
