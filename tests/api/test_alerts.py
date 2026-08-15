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

    async def test_list_alerts_filter_by_status(self, client: AsyncClient) -> None:
        active = await client.get("/api/v1/alerts", params={"status": "active"})
        assert active.status_code == 200
        assert active.json()["count"] == 2
        assert all(item["status"] == "active" for item in active.json()["data"])

        resolved = await client.get("/api/v1/alerts", params={"status": "resolved"})
        assert resolved.status_code == 200
        assert resolved.json()["count"] == 1
        assert resolved.json()["data"][0]["alert_id"] == "a-3"

    async def test_list_alerts_filter_by_category(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/alerts", params={"category": "engine"})
        assert response.status_code == 200
        assert response.json()["count"] == 0

    async def test_list_alerts_filter_by_driver(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/alerts", params={"driver_id": "d-2"})
        assert response.status_code == 200
        payload = response.json()
        assert payload["count"] == 1
        assert payload["data"][0]["alert_id"] == "a-2"

    async def test_list_alerts_filter_by_time_range(self, client: AsyncClient) -> None:
        response = await client.get(
            "/api/v1/alerts",
            params={
                "start_time": "2026-01-02T00:00:00Z",
                "end_time": "2026-01-03T00:00:00Z",
            },
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["count"] == 1
        assert payload["data"][0]["alert_id"] == "a-2"

    async def test_list_alerts_returns_canonical_fields(
        self, client: AsyncClient
    ) -> None:
        response = await client.get("/api/v1/alerts")
        assert response.status_code == 200
        alert = response.json()["data"][0]
        assert "condition" in alert
        assert "category" in alert
        assert "message" in alert
        assert "evidence" in alert
        assert "source" in alert
        assert "acknowledged_at" in alert
        assert alert["source"] == "alert_engine"

    async def test_alert_stats(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/alerts/stats")
        assert response.status_code == 200
        stats = response.json()
        assert stats["total"] == 3
        assert stats["critical_active"] == 1
        assert stats["high_active"] == 1
        assert stats["active"] == 2
        assert stats["acknowledged"] == 2
        assert stats["resolved"] == 1

    async def test_alert_stats_filtered(self, client: AsyncClient) -> None:
        response = await client.get(
            "/api/v1/alerts/stats", params={"severity": "critical"}
        )
        assert response.status_code == 200
        stats = response.json()
        assert stats["total"] == 1
        assert stats["critical_active"] == 1

    async def test_acknowledge_alert(self, client: AsyncClient) -> None:
        response = await client.post("/api/v1/alerts/a-1/acknowledge")
        assert response.status_code == 200
        alert = response.json()
        assert alert["alert_id"] == "a-1"
        assert alert["acknowledged"] is True
        assert alert["acknowledged_at"] is not None
        assert alert["status"] == "active"

        listed = await client.get("/api/v1/alerts")
        assert listed.status_code == 200
        a1 = next(
            item for item in listed.json()["data"] if item["alert_id"] == "a-1"
        )
        assert a1["acknowledged"] is True
        assert a1["acknowledged_at"] is not None

    async def test_acknowledge_alert_is_idempotent(
        self, client: AsyncClient
    ) -> None:
        first = await client.post("/api/v1/alerts/a-1/acknowledge")
        assert first.status_code == 200
        first_ts = first.json()["acknowledged_at"]
        assert first_ts is not None

        second = await client.post("/api/v1/alerts/a-1/acknowledge")
        assert second.status_code == 200
        assert second.json()["acknowledged_at"] == first_ts

    async def test_acknowledge_unknown_alert(self, client: AsyncClient) -> None:
        response = await client.post("/api/v1/alerts/a-99/acknowledge")
        assert response.status_code == 404

    async def test_resolve_alert(self, client: AsyncClient) -> None:
        response = await client.post("/api/v1/alerts/a-1/resolve")
        assert response.status_code == 200
        alert = response.json()
        assert alert["alert_id"] == "a-1"
        assert alert["acknowledged"] is True
        assert alert["acknowledged_at"] is not None
        assert alert["status"] == "resolved"
        assert alert["resolved_at"] is not None

        listed = await client.get("/api/v1/alerts", params={"status": "resolved"})
        assert listed.json()["count"] == 2

    async def test_resolve_alert_is_idempotent(self, client: AsyncClient) -> None:
        first = await client.post("/api/v1/alerts/a-1/resolve")
        assert first.status_code == 200
        first_ack = first.json()["acknowledged_at"]
        first_resolved = first.json()["resolved_at"]

        second = await client.post("/api/v1/alerts/a-1/resolve")
        assert second.status_code == 200
        assert second.json()["acknowledged_at"] == first_ack
        assert second.json()["resolved_at"] == first_resolved

    async def test_resolve_unknown_alert(self, client: AsyncClient) -> None:
        response = await client.post("/api/v1/alerts/a-99/resolve")
        assert response.status_code == 404
