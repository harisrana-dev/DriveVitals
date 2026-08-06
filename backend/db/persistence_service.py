import logging
from collections.abc import Sequence
from datetime import datetime

from backend.analytics.driver_statistics.models.driver_statistics import (
    DriverStatistics,
)
from backend.analytics.snapshot.analytics_snapshot import AnalyticsSnapshot
from backend.analytics.vehicle_health.models.health_snapshot import (
    HealthSnapshot,
)

from backend.alerts.models.fleet_alert import (
    FleetAlert,
)
from backend.fleet.models.driver import Driver as DomainDriver
from backend.fleet.models.route import Route as DomainRoute
from backend.fleet.models.vehicle import Vehicle as DomainVehicle
from backend.maintenance.models.maintenance_record import MaintenanceRecord
from backend.telemetry.models.telemetry_sample import TelemetrySample
from backend.db.repositories import (
    VehicleRepository,
    DriverRepository,
    RouteRepository,
    TripRepository,
    TelemetryRepository,
    BehaviourRepository,
    VehicleHealthRepository,
    DriverStatisticsRepository,
    MaintenanceRepository,
    AlertRepository,
)
from backend.db.session import async_session_factory

logger = logging.getLogger(__name__)


class PersistenceService:

    def __init__(self) -> None:
        pass

    async def persist_vehicle(self, vehicle: DomainVehicle) -> None:
        try:
            async with async_session_factory() as session:
                repo = VehicleRepository(session)
                await repo.upsert(
                    vehicle_id=vehicle.vehicle_id,
                    manufacturer=vehicle.make,
                    model=vehicle.model,
                    year=vehicle.year,
                    status="active",
                )
                await session.commit()
        except Exception:
            logger.exception("Failed to persist vehicle %s", vehicle.vehicle_id)

    async def persist_driver(self, driver: DomainDriver) -> None:
        try:
            async with async_session_factory() as session:
                repo = DriverRepository(session)
                parts = driver.name.strip().split(" ", 1)
                first_name = parts[0] if parts else driver.name
                last_name = parts[1] if len(parts) > 1 else ""
                await repo.upsert(
                    driver_id=driver.driver_id,
                    first_name=first_name,
                    last_name=last_name,
                    employment_status="active",
                )
                await session.commit()
        except Exception:
            logger.exception("Failed to persist driver %s", driver.driver_id)

    async def persist_route(self, route: DomainRoute) -> None:
        try:
            async with async_session_factory() as session:
                repo = RouteRepository(session)
                await repo.upsert(
                    route_id=route.route_id,
                    name=f"{route.origin} \u2192 {route.destination}",
                    route_type=route.route_type.value if hasattr(route.route_type, "value") else str(route.route_type),
                    origin=route.origin,
                    destination=route.destination,
                    estimated_distance_km=route.distance_km,
                )
                await session.commit()
        except Exception:
            logger.exception("Failed to persist route %s", route.route_id)

    async def create_trip(
        self,
        trip_id: str,
        vehicle_id: str,
        driver_id: str,
        route_id: str,
        start_time: datetime,
    ) -> None:
        async with async_session_factory() as session:
            repo = TripRepository(session)
            existing = await repo.get_by_id(trip_id)
            if existing is not None:
                logger.info("Trip %s already exists, skipping creation", trip_id)
                return
            await repo.create(
                trip_id=trip_id,
                vehicle_id=vehicle_id,
                driver_id=driver_id,
                route_id=route_id,
                start_time=start_time,
                status="in_progress",
            )
            await session.commit()
            logger.info("Trip %s created", trip_id)

    async def complete_trip(
        self,
        trip_id: str,
        end_time: datetime,
        distance_km: float,
        duration_seconds: int,
        fuel_used_liters: float,
        average_speed_kmh: float,
        maximum_speed_kmh: float,
        trip_score: float | None = None,
    ) -> None:
        try:
            async with async_session_factory() as session:
                repo = TripRepository(session)
                await repo.complete(
                    trip_id=trip_id,
                    end_time=end_time,
                    distance_km=distance_km,
                    duration_seconds=duration_seconds,
                    fuel_used_liters=fuel_used_liters,
                    average_speed_kmh=average_speed_kmh,
                    maximum_speed_kmh=maximum_speed_kmh,
                    trip_score=trip_score,
                )
                await session.commit()
        except Exception:
            logger.exception("Failed to complete trip %s", trip_id)

    async def persist_telemetry(self, sample: TelemetrySample) -> None:
        try:
            async with async_session_factory() as session:
                repo = TelemetryRepository(session)
                await repo.insert(
                    trip_id=sample.trip_id,
                    vehicle_id=sample.vehicle_id,
                    timestamp=sample.timestamp,
                    speed_kmh=sample.speed_kmh,
                    rpm=sample.rpm,
                    engine_load_percent=sample.engine_load_percent,
                    throttle_percent=sample.throttle_position_percent,
                    brake_percent=sample.brake_pressure,
                    fuel_rate_lph=sample.fuel_rate_lph,
                    fuel_level_percent=sample.fuel_level_percent,
                    coolant_temperature_c=sample.coolant_temperature_c,
                    odometer_km=sample.odometer_km,
                )
                await session.commit()
        except Exception:
            logger.exception(
                "Failed to persist telemetry for trip %s", sample.trip_id
            )

    async def persist_behaviour_events(
        self,
        snapshot: AnalyticsSnapshot,
    ) -> None:
        try:
            if not snapshot.completed_events:
                return
            async with async_session_factory() as session:
                repo = BehaviourRepository(session)
                for event in snapshot.completed_events:
                    await repo.insert(
                        trip_id=snapshot.trip_id,
                        vehicle_id=snapshot.vehicle_id,
                        driver_id=snapshot.driver_id,
                        event_type=event.event_type,
                        severity=event.severity,
                        started_at=event.started_at,
                        ended_at=event.ended_at,
                        duration_seconds=event.duration_seconds,
                        distance_km=event.distance_km,
                        maximum_value=event.max_speed_excess_kmh or event.max_rpm or event.max_throttle_percent or event.max_braking_intensity or 0.0,
                        average_value=0.0,
                    )
                await session.commit()
        except Exception:
            logger.exception(
                "Failed to persist behaviour events for vehicle %s",
                snapshot.vehicle_id,
            )

    async def persist_vehicle_health(
        self,
        health_snapshot: HealthSnapshot,
    ) -> None:
        try:
            async with async_session_factory() as session:
                repo = VehicleHealthRepository(session)
                await repo.upsert(
                    vehicle_id=health_snapshot.vehicle_id,
                    overall_health_score=health_snapshot.overall_health_score,
                    engine_health=health_snapshot.engine_health.score,
                    brake_health=health_snapshot.brake_health.score,
                    transmission_health=health_snapshot.transmission_health.score,
                    cooling_health=health_snapshot.cooling_health.score,
                    fuel_system_health=health_snapshot.fuel_system_health.score,
                    last_updated=health_snapshot.timestamp,
                )
                await session.commit()
        except Exception:
            logger.exception(
                "Failed to persist vehicle health for %s",
                health_snapshot.vehicle_id,
            )

    async def persist_driver_statistics(
        self,
        statistics: DriverStatistics,
    ) -> None:
        try:
            async with async_session_factory() as session:
                repo = DriverStatisticsRepository(session)
                await repo.upsert(
                    driver_id=statistics.driver_id,
                    safety_score=statistics.safety_score,
                    aggression_score=statistics.aggression_score,
                    efficiency_score=statistics.efficiency_score,
                    speeding_events=statistics.overspeed_count,
                    harsh_braking_events=statistics.harsh_braking_count,
                    aggressive_throttle_events=(
                        statistics.harsh_acceleration_count
                    ),
                    high_rpm_events=max(
                        0,
                        statistics.total_events
                        - statistics.harsh_braking_count
                        - statistics.overspeed_count
                        - statistics.harsh_acceleration_count,
                    ),
                    total_distance_km=statistics.total_distance,
                    total_trips=statistics.total_trips,
                )
                await session.commit()
        except Exception:
            logger.exception(
                "Failed to persist driver statistics for %s",
                statistics.driver_id,
            )

    async def persist_maintenance_records(
        self,
        records: Sequence[MaintenanceRecord],
    ) -> None:
        try:
            if not records:
                return
            async with async_session_factory() as session:
                repo = MaintenanceRepository(session)
                for record in records:
                    await repo.upsert(
                        maintenance_id=record.maintenance_id,
                        vehicle_id=record.vehicle_id,
                        maintenance_type=(
                            record.maintenance_type.value
                            if hasattr(record.maintenance_type, "value")
                            else str(record.maintenance_type)
                        ),
                        priority=(
                            record.priority.value
                            if hasattr(record.priority, "value")
                            else str(record.priority)
                        ),
                        status="pending",
                        due_odometer_km=record.odometer_km,
                        created_at=record.performed_at,
                    )
                await session.commit()
        except Exception:
            logger.exception(
                "Failed to persist %d maintenance record(s)",
                len(records),
            )

    async def persist_alerts(
        self,
        alerts: Sequence[FleetAlert],
    ) -> None:
        try:
            if not alerts:
                return
            async with async_session_factory() as session:
                repo = AlertRepository(session)
                for alert in alerts:
                    await repo.upsert(
                        alert_id=alert.alert_id,
                        vehicle_id=alert.vehicle_id,
                        alert_type=(
                            alert.alert_type.value
                            if hasattr(alert.alert_type, "value")
                            else str(alert.alert_type)
                        ),
                        severity=(
                            alert.severity.value
                            if hasattr(alert.severity, "value")
                            else str(alert.severity)
                        ),
                        message=alert.message,
                        created_at=alert.created_at,
                        driver_id=alert.driver_id,
                        trip_id=alert.trip_id,
                    )
                await session.commit()
        except Exception:
            logger.exception(
                "Failed to persist %d alert(s)",
                len(alerts),
            )

    async def resolve_cleared_alerts(
        self,
        vehicle_id: str,
        categories: Sequence[str],
        active_alert_ids: Sequence[str] = (),
    ) -> int:
        """Resolve open alerts whose condition is no longer active.

        ``active_alert_ids`` are the canonical condition keys currently
        triggered for the vehicle (evaluated before duplicate suppression).
        Open alerts in ``categories`` that are not in that set transition to
        ``resolved``; history is preserved.
        """
        try:
            async with async_session_factory() as session:
                repo = AlertRepository(session)
                resolved = await repo.resolve_stale(
                    vehicle_id=vehicle_id,
                    categories=categories,
                    active_alert_ids=active_alert_ids,
                )
                if resolved:
                    await session.commit()
                    logger.info(
                        "Resolved %d cleared alert(s) for vehicle %s",
                        resolved,
                        vehicle_id,
                    )
                return resolved
        except Exception:
            logger.exception(
                "Failed to resolve cleared alerts for vehicle %s",
                vehicle_id,
            )
            return 0
