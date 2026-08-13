"""
Driver Statistics Reconciler.

Rebuilds the persisted ``driver_statistics`` materialized cache from the
canonical source of truth — completed trips plus their behaviour events —
and re-seeds the in-memory accumulator used by
:class:`DriverStatisticsConsumer`.

Without this step the consumer's accumulator starts empty on every
restart, so the first trip completion after a restart recomputes
statistics from a single trip and OVERWRITES the driver's full recorded
history (total trips, distance, and density-derived scores) in the DB.
"""

import logging
from collections import defaultdict

from backend.analytics.behaviour.events.event import (
    BehaviourEvent,
)
from backend.analytics.driver_statistics.driver_statistics_engine import (
    DriverStatisticsEngine,
)
from backend.application.consumers.driver_statistics_consumer import (
    DriverStatisticsConsumer,
)
from backend.db.models.behaviour_event import (
    BehaviourEvent as DBBehaviourEvent,
)
from backend.db.models.trip import Trip as DBTrip
from backend.db.repositories import (
    BehaviourRepository,
    TripRepository,
)
from backend.db.session import async_session_factory
from backend.fleet.models.trip import (
    Trip,
    TripStatus,
)

logger = logging.getLogger(__name__)


def _to_domain_trip(db_trip: DBTrip) -> Trip:
    return Trip(
        trip_id=db_trip.trip_id,
        vehicle_id=db_trip.vehicle_id,
        driver_id=db_trip.driver_id,
        route_id=db_trip.route_id,
        status=TripStatus.COMPLETED,
        started_at=db_trip.start_time,
        completed_at=db_trip.end_time,
        distance_travelled_km=db_trip.distance_km or 0.0,
        fuel_used_liters=db_trip.fuel_used_liters or 0.0,
        maximum_speed_kmh=db_trip.maximum_speed_kmh or 0.0,
        trip_score=db_trip.trip_score,
    )


def _to_domain_event(db_event: DBBehaviourEvent) -> BehaviourEvent:
    return BehaviourEvent(
        vehicle_id=db_event.vehicle_id,
        driver_id=db_event.driver_id,
        trip_id=db_event.trip_id,
        event_type=db_event.event_type,
        started_at=db_event.started_at,
        ended_at=db_event.ended_at,
        duration_seconds=db_event.duration_seconds,
        distance_km=db_event.distance_km,
        severity=db_event.severity,
    )


class DriverStatisticsReconciler:
    """
    Purpose:
        Recompute persisted driver statistics from completed trips and
        their behaviour events, and seed the runtime consumer with the
        same history.
    Inputs:
        Completed trips + behaviour events from the database.
    Outputs:
        Updated ``driver_statistics`` rows and a warm consumer
        accumulator.
    """

    def __init__(
        self,
        *,
        engine: DriverStatisticsEngine,
        consumer: DriverStatisticsConsumer,
    ) -> None:
        self._engine = engine
        self._consumer = consumer

    async def reconcile(
        self,
        persistence,
    ) -> int:
        """
        Rebuild statistics for every driver with at least one completed
        trip and re-seed the consumer's accumulator.

        Returns the number of drivers reconciled.
        """
        async with async_session_factory() as session:
            trips = await TripRepository(session).list_completed()
            events = await BehaviourRepository(session).list_by_trip_ids(
                [trip.trip_id for trip in trips]
            )

        trips_by_driver: dict[str, list[Trip]] = defaultdict(list)
        events_by_driver: dict[str, list[BehaviourEvent]] = defaultdict(list)

        for db_trip in trips:
            trips_by_driver[db_trip.driver_id].append(
                _to_domain_trip(db_trip)
            )
        for db_event in events:
            events_by_driver[db_event.driver_id].append(
                _to_domain_event(db_event)
            )

        for driver_id, domain_trips in trips_by_driver.items():
            domain_events = events_by_driver.get(driver_id, [])
            try:
                statistics = self._engine.compute_statistics(
                    driver_id=driver_id,
                    behaviour_events=domain_events,
                    trips=domain_trips,
                )
            except Exception:
                logger.exception(
                    "Driver statistics reconcile failed for driver %s",
                    driver_id,
                )
                continue

            self._consumer.seed(
                driver_id=driver_id,
                behaviour_events=domain_events,
                trips=domain_trips,
            )

            if persistence is not None:
                await persistence.persist_driver_statistics(statistics)

        if trips_by_driver:
            logger.info(
                "Reconciled driver statistics for %d driver(s)",
                len(trips_by_driver),
            )

        return len(trips_by_driver)
