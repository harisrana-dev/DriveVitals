from httpx import AsyncClient
from sqlalchemy import select

from backend.db.models.alert import Alert
from backend.db.models.behaviour_event import BehaviourEvent
from backend.db.models.driver import Driver
from backend.db.models.route import Route
from backend.db.models.telemetry_sample import TelemetrySample
from backend.db.models.trip import Trip
from backend.db.models.vehicle import Vehicle
from tests.api.conftest import test_session_factory as _session_factory


async def _abort(trip_id: str) -> None:
    """Flip an existing trip to ``aborted`` directly in the database."""
    async with _session_factory() as session:
        trip = await session.get(Trip, trip_id)
        assert trip is not None
        trip.status = "aborted"
        await session.commit()


async def _child_counts(trip_id: str) -> dict[str, int]:
    async with _session_factory() as session:
        telemetry = await session.execute(
            select(TelemetrySample).where(TelemetrySample.trip_id == trip_id)
        )
        events = await session.execute(
            select(BehaviourEvent).where(BehaviourEvent.trip_id == trip_id)
        )
        alerts = await session.execute(
            select(Alert).where(Alert.trip_id == trip_id)
        )
        return {
            "telemetry": len(telemetry.scalars().all()),
            "behaviour": len(events.scalars().all()),
            "alerts": len(alerts.scalars().all()),
        }


class TestDeleteTrip:

    async def test_delete_aborted_trip(self, operator_client: AsyncClient) -> None:
        response = await operator_client.delete("/api/v1/trips/t-5")

        assert response.status_code == 204

        got = await operator_client.get("/api/v1/trips/t-5")
        assert got.status_code == 404

        listing = await operator_client.get("/api/v1/trips")
        assert listing.status_code == 200
        assert listing.json()["count"] == 4
        assert {t["trip_id"] for t in listing.json()["data"]} == {
            "t-1",
            "t-2",
            "t-3",
            "t-4",
        }

    async def test_delete_aborted_trip_second_delete_is_404(
        self, operator_client: AsyncClient
    ) -> None:
        first = await operator_client.delete("/api/v1/trips/t-5")
        assert first.status_code == 204

        second = await operator_client.delete("/api/v1/trips/t-5")
        assert second.status_code == 404

    async def test_delete_completed_trip_rejected(
        self, operator_client: AsyncClient
    ) -> None:
        response = await operator_client.delete("/api/v1/trips/t-1")

        assert response.status_code == 409
        assert "Only aborted trips" in response.json()["detail"]

        got = await operator_client.get("/api/v1/trips/t-1")
        assert got.status_code == 200

    async def test_delete_in_progress_trip_rejected(
        self, operator_client: AsyncClient
    ) -> None:
        response = await operator_client.delete("/api/v1/trips/t-3")

        assert response.status_code == 409
        assert "in_progress" in response.json()["detail"]

        got = await operator_client.get("/api/v1/trips/t-3")
        assert got.status_code == 200

    async def test_delete_unknown_trip_404(
        self, operator_client: AsyncClient
    ) -> None:
        response = await operator_client.delete("/api/v1/trips/does-not-exist")

        assert response.status_code == 404

    async def test_delete_aborted_trip_removes_trip_scoped_children_only(
        self, operator_client: AsyncClient
    ) -> None:
        await _abort("t-1")
        assert await _child_counts("t-1") == {
            "telemetry": 3,
            "behaviour": 3,
            "alerts": 2,
        }

        response = await operator_client.delete("/api/v1/trips/t-1")
        assert response.status_code == 204

        assert await _child_counts("t-1") == {
            "telemetry": 0,
            "behaviour": 0,
            "alerts": 0,
        }

        async with _session_factory() as session:
            trips = (await session.execute(select(Trip))).scalars().all()
            assert {t.trip_id for t in trips} == {"t-2", "t-3", "t-4", "t-5"}

            vehicles = (await session.execute(select(Vehicle))).scalars().all()
            assert len(vehicles) == 5

            drivers = (await session.execute(select(Driver))).scalars().all()
            assert len(drivers) == 3

            routes = (await session.execute(select(Route))).scalars().all()
            assert len(routes) == 3

            untouched = await session.execute(
                select(TelemetrySample).where(TelemetrySample.trip_id == "t-3")
            )
            assert len(untouched.scalars().all()) == 2


class TestDeleteAllAborted:

    async def test_bulk_delete_aborted(
        self, operator_client: AsyncClient
    ) -> None:
        response = await operator_client.delete("/api/v1/trips/aborted")

        assert response.status_code == 200
        assert response.json() == {"deleted_count": 1}

        listing = await operator_client.get("/api/v1/trips")
        assert listing.status_code == 200
        assert listing.json()["count"] == 4
        assert {t["trip_id"] for t in listing.json()["data"]} == {
            "t-1",
            "t-2",
            "t-3",
            "t-4",
        }

    async def test_bulk_delete_aborted_is_idempotent(
        self, operator_client: AsyncClient
    ) -> None:
        first = await operator_client.delete("/api/v1/trips/aborted")
        assert first.json() == {"deleted_count": 1}

        second = await operator_client.delete("/api/v1/trips/aborted")
        assert second.status_code == 200
        assert second.json() == {"deleted_count": 0}

    async def test_bulk_delete_aborted_removes_children(
        self, operator_client: AsyncClient
    ) -> None:
        await _abort("t-1")
        await _abort("t-3")

        response = await operator_client.delete("/api/v1/trips/aborted")

        assert response.status_code == 200
        assert response.json() == {"deleted_count": 3}

        assert await _child_counts("t-1") == {
            "telemetry": 0,
            "behaviour": 0,
            "alerts": 0,
        }
        assert await _child_counts("t-3") == {
            "telemetry": 0,
            "behaviour": 0,
            "alerts": 0,
        }

        async with _session_factory() as session:
            trips = (await session.execute(select(Trip))).scalars().all()
            assert {t.trip_id for t in trips} == {"t-2", "t-4"}

    async def test_bulk_delete_aborted_empty_database(
        self, operator_empty_client: AsyncClient
    ) -> None:
        response = await operator_empty_client.delete("/api/v1/trips/aborted")

        assert response.status_code == 200
        assert response.json() == {"deleted_count": 0}


class TestPaginationRegression:

    async def test_pagination_reconciles_after_individual_delete(
        self, operator_client: AsyncClient
    ) -> None:
        await operator_client.delete("/api/v1/trips/t-5")

        collected: list[str] = []
        offset = 0
        while True:
            response = await operator_client.get(
                "/api/v1/trips", params={"limit": 2, "offset": offset}
            )
            assert response.status_code == 200
            payload = response.json()
            collected.extend(item["trip_id"] for item in payload["data"])
            assert payload["count"] == 4
            if offset + len(payload["data"]) >= payload["count"]:
                break
            offset += len(payload["data"])

        assert set(collected) == {"t-1", "t-2", "t-3", "t-4"}

    async def test_pagination_reconciles_after_bulk_delete(
        self, operator_client: AsyncClient
    ) -> None:
        await operator_client.delete("/api/v1/trips/aborted")

        response = await operator_client.get(
            "/api/v1/trips", params={"limit": 2, "offset": 2}
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["count"] == 4
        assert len(payload["data"]) == 2

    async def test_kpi_aggregates_exclude_deleted_trips(
        self, operator_client: AsyncClient
    ) -> None:
        """Deleting an aborted trip must not change completed-trip metrics."""
        before = await operator_client.get("/api/v1/trips", params={"status": "completed"})
        assert before.status_code == 200
        before_count = before.json()["count"]

        await operator_client.delete("/api/v1/trips/t-5")

        after = await operator_client.get("/api/v1/trips", params={"status": "completed"})
        assert after.status_code == 200
        assert after.json()["count"] == before_count == 3
