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

    async def test_list_maintenance_filter_by_status(self, client: AsyncClient) -> None:
        response = await client.get(
            "/api/v1/maintenance", params={"status": "pending"}
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["count"] == 2

    async def test_list_maintenance_filter_by_status_completed(
        self, client: AsyncClient
    ) -> None:
        response = await client.get(
            "/api/v1/maintenance", params={"status": "completed"}
        )

        assert response.status_code == 200
        assert response.json() == {"data": [], "count": 0}

    async def test_list_maintenance_exposes_data_trust_fields(
        self, client: AsyncClient
    ) -> None:
        response = await client.get("/api/v1/maintenance")

        assert response.status_code == 200
        item = response.json()["data"][0]
        for field in (
            "due_date",
            "component",
            "reason",
            "recommended_action",
            "estimated_cost",
        ):
            assert field in item

    async def test_list_maintenance_sort_by_due_odometer(
        self, client: AsyncClient
    ) -> None:
        response = await client.get(
            "/api/v1/maintenance", params={"sort": "due_odometer_km"}
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["count"] == 2
        odometers = [item["due_odometer_km"] for item in payload["data"]]
        assert odometers == sorted(odometers)

    async def test_complete_maintenance(self, client: AsyncClient) -> None:
        mid = (
            await client.get("/api/v1/maintenance", params={"limit": 1})
        ).json()["data"][0]["maintenance_id"]

        response = await client.patch(
            f"/api/v1/maintenance/{mid}/complete",
            json={"completed_odometer_km": 99999.0},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "completed"
        assert body["completed_odometer_km"] == 99999.0
        assert body["completed_at"] is not None

    async def test_complete_maintenance_idempotent(
        self, client: AsyncClient
    ) -> None:
        mid = (
            await client.get("/api/v1/maintenance", params={"limit": 1})
        ).json()["data"][0]["maintenance_id"]

        first = await client.patch(
            f"/api/v1/maintenance/{mid}/complete", json={}
        )
        second = await client.patch(
            f"/api/v1/maintenance/{mid}/complete", json={}
        )

        assert first.status_code == 200
        assert second.status_code == 200
        assert first.json()["completed_at"] == second.json()["completed_at"]
        assert first.json()["completed_odometer_km"] == second.json()[
            "completed_odometer_km"
        ]

    async def test_complete_maintenance_defaults_odometer_to_due(
        self, client: AsyncClient
    ) -> None:
        mid = (
            await client.get("/api/v1/maintenance", params={"limit": 1})
        ).json()["data"][0]["maintenance_id"]
        due = (
            await client.get("/api/v1/maintenance", params={"limit": 1})
        ).json()["data"][0]["due_odometer_km"]

        response = await client.patch(
            f"/api/v1/maintenance/{mid}/complete", json={}
        )

        assert response.status_code == 200
        assert response.json()["completed_odometer_km"] == due

    async def test_complete_maintenance_not_found(
        self, client: AsyncClient
    ) -> None:
        response = await client.patch(
            "/api/v1/maintenance/missing/complete", json={}
        )

        assert response.status_code == 404
