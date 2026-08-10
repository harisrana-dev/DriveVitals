from httpx import AsyncClient


class TestTrips:

    async def test_list_trips(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/trips")

        assert response.status_code == 200
        payload = response.json()
        assert payload["count"] == 5
        assert len(payload["data"]) == 5

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
        assert in_progress.json()["count"] == 2
        assert {
            item["status"] for item in in_progress.json()["data"]
        } == {"in_progress", "aborted"}

    async def test_list_trips_pagination(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/trips", params={"limit": 2, "offset": 2})

        assert response.status_code == 200
        payload = response.json()
        assert len(payload["data"]) == 2
        assert payload["count"] == 5

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

    async def test_get_trip_completed_contract(self, client: AsyncClient) -> None:
        """Completed trips expose the unified REST/WS trip contract."""
        response = await client.get("/api/v1/trips/t-1")

        assert response.status_code == 200
        trip = response.json()["data"]

        assert trip["trip_id"] == "t-1"
        assert trip["status"] == "completed"

        assert trip["vehicle_id"] == "v-1"
        assert trip["vehicle_name"] == "2024 Test Transit"
        assert trip["driver_id"] == "d-1"
        assert trip["driver_name"] == "Alice Smith"
        assert trip["route_id"] == "r-1"
        assert trip["route_name"] == "Warehouse to Customer A"
        assert trip["route_type"] == "urban"

        assert trip["started_at"] == "2026-01-01T08:00:00Z"
        assert trip["completed_at"] == "2026-01-01T09:00:00Z"

        assert trip["distance_km"] == 12.5
        assert trip["duration_seconds"] == 3600
        assert trip["fuel_consumed_liters"] == 2.5
        assert trip["average_speed_kmh"] == 12.5
        assert trip["maximum_speed_kmh"] == 55.0
        assert trip["average_fuel_rate_lph"] == 2.5
        assert trip["safety_score"] == 85.0
        assert trip["grade"] == "B"

        assert trip["speeding_event_count"] == 1
        assert trip["speeding_duration_seconds"] == 20.0
        assert trip["harsh_braking_count"] == 1
        assert trip["aggressive_throttle_event_count"] == 1
        assert trip["aggressive_throttle_duration_seconds"] == 10.0
        assert trip["high_rpm_event_count"] == 0
        assert trip["high_rpm_duration_seconds"] == 0.0
        assert trip["severe_event_count"] == 0
        assert trip["moderate_event_count"] == 2
        assert trip["minor_event_count"] == 1
        assert trip["overall_severity"] == "moderate"

        assert len(trip["events"]) == 3
        assert {e["event_type"] for e in trip["events"]} == {
            "speeding",
            "harsh_braking",
            "aggressive_throttle",
        }
        speeding = next(e for e in trip["events"] if e["event_type"] == "speeding")
        assert speeding["duration_seconds"] == 20.0
        assert speeding["severity"] == "moderate"

    async def test_get_trip_active_contract(self, client: AsyncClient) -> None:
        """In-progress trips leave completion-only metrics as null, never 0."""
        response = await client.get("/api/v1/trips/t-3")

        assert response.status_code == 200
        trip = response.json()["data"]

        assert trip["trip_id"] == "t-3"
        assert trip["status"] == "in_progress"
        assert trip["completed_at"] is None
        assert trip["distance_km"] is None
        assert trip["duration_seconds"] is None
        assert trip["fuel_consumed_liters"] is None
        assert trip["average_speed_kmh"] is None
        assert trip["maximum_speed_kmh"] is None
        assert trip["safety_score"] is None
        assert trip["grade"] is None
        assert trip["average_fuel_rate_lph"] is None

    async def test_get_trip_aborted(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/trips/t-5")

        assert response.status_code == 200
        trip = response.json()["data"]
        assert trip["trip_id"] == "t-5"
        assert trip["status"] == "aborted"
        assert trip["vehicle_name"] == "2022 Test Volvo"
        assert trip["driver_name"] == "Carol Lee"
        assert trip["completed_at"] == "2026-01-05T08:30:00Z"
        assert trip["safety_score"] is None
        assert trip["grade"] is None
        assert trip["events"] == []

    async def test_list_trips_filter_by_status(self, client: AsyncClient) -> None:
        for status, expected in {
            "completed": {"t-1", "t-2", "t-4"},
            "in_progress": {"t-3"},
            "aborted": {"t-5"},
        }.items():
            response = await client.get("/api/v1/trips", params={"status": status})

            assert response.status_code == 200
            payload = response.json()
            assert {item["trip_id"] for item in payload["data"]} == expected
            assert all(item["status"] == status for item in payload["data"])

    async def test_list_trips_filter_by_multiple_statuses(
        self, client: AsyncClient
    ) -> None:
        response = await client.get(
            "/api/v1/trips", params={"status": "completed,aborted"}
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["count"] == 4
        assert {item["trip_id"] for item in payload["data"]} == {
            "t-1",
            "t-2",
            "t-4",
            "t-5",
        }
        assert {item["status"] for item in payload["data"]} == {
            "completed",
            "aborted",
        }

    async def test_list_trips_status_precedence_over_completed(
        self, client: AsyncClient
    ) -> None:
        response = await client.get(
            "/api/v1/trips",
            params={"status": "aborted", "completed": "true"},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["count"] == 1
        assert {item["trip_id"] for item in payload["data"]} == {"t-5"}

    async def test_list_trips_filter_by_route_type(self, client: AsyncClient) -> None:
        response = await client.get(
            "/api/v1/trips", params={"route_type": "urban"}
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["count"] == 3
        assert {item["trip_id"] for item in payload["data"]} == {"t-1", "t-3", "t-4"}
        assert all(item["route_type"] == "urban" for item in payload["data"])

    async def test_list_trips_deterministic_ordering(self, client: AsyncClient) -> None:
        """Trips are ordered by start_time DESC with a stable secondary key."""
        response = await client.get(
            "/api/v1/trips", params={"limit": 100}
        )

        assert response.status_code == 200
        payload = response.json()
        ids = [item["trip_id"] for item in payload["data"]]

        assert ids == sorted(
            ids, key=lambda tid: {
                "t-5": "2026-01-05T08:00:00Z",
                "t-4": "2026-01-04T08:00:00Z",
                "t-3": "2026-01-03T08:00:00Z",
                "t-2": "2026-01-02T08:00:00Z",
                "t-1": "2026-01-01T08:00:00Z",
            }[tid],
            reverse=True,
        )

    async def test_list_trips_status_pagination(self, client: AsyncClient) -> None:
        response = await client.get(
            "/api/v1/trips",
            params={"status": "completed,aborted", "limit": 2, "offset": 2},
        )

        assert response.status_code == 200
        payload = response.json()
        assert len(payload["data"]) == 2
        assert payload["count"] == 4
        assert {item["trip_id"] for item in payload["data"]} == {"t-2", "t-1"}
