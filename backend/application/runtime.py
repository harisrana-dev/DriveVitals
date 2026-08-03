import asyncio
import logging
import uuid

from datetime import (
    datetime,
    timedelta,
    timezone,
)

from backend.analytics.behaviour.aggregation.summary import (
    DriverBehaviourSummary,
)

from backend.analytics.behaviour.aggregation.summarizer import (
    DriverBehaviourSummarizer,
)

from backend.analytics.behaviour.detection.analyzer import (
    DriverBehaviourAnalyzer,
)

from backend.analytics.behaviour.events.tracker import (
    BehaviourEventTracker,
)

from backend.analytics.context.analytics_context import (
    AnalyticsContext,
)

from backend.analytics.context.context_store import (
    AnalyticsContextStore,
)

from backend.analytics.driver_statistics.aggregators.driver_score_calculator import (
    DriverScoreCalculator,
)

from backend.analytics.driver_statistics.driver_statistics_engine import (
    DriverStatisticsEngine,
)

from backend.analytics.engine import (
    AnalyticsEngine,
)

from backend.analytics.snapshot.analytics_snapshot import (
    AnalyticsSnapshot,
)

from backend.analytics.snapshot.snapshot_store import (
    AnalyticsSnapshotStore,
)

from backend.analytics.state.runtime_state_store import (
    RuntimeStateStore,
)

from backend.analytics.vehicle_health.analyzers.brake_health import (
    BrakeHealthAnalyzer,
)
from backend.analytics.vehicle_health.analyzers.cooling_health import (
    CoolingHealthAnalyzer,
)
from backend.analytics.vehicle_health.analyzers.engine_health import (
    EngineHealthAnalyzer,
)
from backend.analytics.vehicle_health.analyzers.fuel_system_health import (
    FuelSystemHealthAnalyzer,
)
from backend.analytics.vehicle_health.analyzers.transmission_health import (
    TransmissionHealthAnalyzer,
)
from backend.analytics.vehicle_health.vehicle_health_engine import (
    VehicleHealthEngine,
)

from backend.alerts.alert_engine import (
    AlertEngine,
)
from backend.alerts.generators import (
    HealthAlertsGenerator,
    MaintenanceAlertsGenerator,
    TelemetryAlertsGenerator,
    TripAlertsGenerator,
)

from backend.application.consumers.driver_statistics_consumer import (
    DriverStatisticsConsumer,
)
from backend.application.consumers.vehicle_health_consumer import (
    VehicleHealthConsumer,
)
from backend.application.intelligence_state import (
    IntelligenceState,
)

from backend.db.persistence_service import (
    PersistenceService,
)

from backend.fleet.config.fleet_factory import (
    FleetConfiguration,
    FleetFactory,
)

from backend.fleet.models.trip import (
    Trip,
)

from backend.fleet.runtime.fleet_runner import (
    FleetRunner,
)

from backend.maintenance.estimators import (
    BrakeEstimator,
    CoolingEstimator,
    EngineEstimator,
    FuelSystemEstimator,
    TransmissionEstimator,
)
from backend.maintenance.maintenance_service import (
    MaintenanceService,
)

from backend.pipeline.telemetry_pipeline import (
    TelemetryPipeline,
    TelemetryConsumer,
)

from backend.streaming.snapshot_stream import (
    AnalyticsSnapshotStream,
    AnalyticsSnapshotSubscriber,
)

from backend.dashboard.services.dashboard_builder import (
    DashboardBuilder,
)

from backend.telemetry.models.telemetry_sample import (
    TelemetrySample,
)

from typing import Any, Callable


TripFlushCallback = Callable[[str, str, Any, Any, list], None]

logger = logging.getLogger(__name__)


def _compute_safety_score(summary: DriverBehaviourSummary) -> float:
    score = 100.0
    score -= summary.speeding_event_count * 5
    score -= summary.harsh_braking_count * 4
    score -= summary.aggressive_throttle_event_count * 4
    score -= summary.high_rpm_event_count * 3
    score -= summary.severe_event_count * 8
    score -= summary.moderate_event_count * 4
    return max(0.0, min(100.0, score))


class DriveVitalsRuntime:
    """
    Composes and runs the DriveVitals application runtime.

    Runtime flow:

        FleetRunner
            ↓
        TelemetrySample
            ↓
        TelemetryPipeline
            ↓
        AnalyticsEngine
            ↓
        AnalyticsSnapshot
            ↓
        AnalyticsSnapshotStream

    The runtime does not know about:

        - FastAPI
        - WebSockets
        - frontend clients
        - HTTP routes
    """

    def __init__(
        self,
        tick_seconds: float = 1.0,
        persistence_service: PersistenceService | None = None,
    ) -> None:

        self._tick_seconds = (
            tick_seconds
        )

        self._persistence_service = persistence_service
        self._fleet_config: FleetConfiguration | None = None

        # --------------------------------------------------------------
        # Fleet runtime
        # --------------------------------------------------------------

        self._fleet = (
            FleetRunner(
                tick_seconds=tick_seconds
            )
        )

        # --------------------------------------------------------------
        # Telemetry pipeline
        # --------------------------------------------------------------

        self._telemetry_pipeline = (
            TelemetryPipeline()
        )

        # --------------------------------------------------------------
        # Analytics dependencies
        # --------------------------------------------------------------

        self._runtime_store = (
            RuntimeStateStore()
        )

        self._context_store = (
            AnalyticsContextStore()
        )

        self._driver_behaviour_analyzer = (
            DriverBehaviourAnalyzer()
        )

        self._event_tracker = (
            BehaviourEventTracker()
        )

        self._behaviour_summarizer = (
            DriverBehaviourSummarizer()
        )

        self._snapshot_store = (
            AnalyticsSnapshotStore()
        )

        self._snapshot_stream = (
            AnalyticsSnapshotStream()
        )

        # --------------------------------------------------------------
        # Dashboard builder
        # --------------------------------------------------------------

        self._dashboard_builder = (
            DashboardBuilder(
                context_store=(
                    self._context_store
                )
            )
        )

        # --------------------------------------------------------------
        # Analytics engine
        # --------------------------------------------------------------

        self._analytics_engine = (
            AnalyticsEngine(
                runtime_store=(
                    self._runtime_store
                ),
                context_store=(
                    self._context_store
                ),
                driver_behaviour_analyzer=(
                    self._driver_behaviour_analyzer
                ),
                event_tracker=(
                    self._event_tracker
                ),
                behaviour_summarizer=(
                    self._behaviour_summarizer
                ),
                snapshot_store=(
                    self._snapshot_store
                ),
                snapshot_stream=(
                    self._snapshot_stream
                ),
            )
        )

        # --------------------------------------------------------------
        # Connect analytics to telemetry pipeline
        # --------------------------------------------------------------

        self._telemetry_pipeline.register(
            self._analytics_engine
        )

        # --------------------------------------------------------------
        # Fleet intelligence (vehicle health + driver statistics)
        #
        # VehicleHealthConsumer is registered AFTER the analytics engine
        # so the AnalyticsSnapshot for each sample is available before
        # vehicle health is evaluated.
        # --------------------------------------------------------------

        self._intelligence_state = (
            IntelligenceState()
        )

        self._vehicle_health_engine = (
            VehicleHealthEngine(
                analyzers=(
                    EngineHealthAnalyzer(),
                    BrakeHealthAnalyzer(),
                    CoolingHealthAnalyzer(),
                    TransmissionHealthAnalyzer(),
                    FuelSystemHealthAnalyzer(),
                )
            )
        )

        self._vehicle_health_consumer = (
            VehicleHealthConsumer(
                engine=(
                    self._vehicle_health_engine
                ),
                snapshot_store=(
                    self._snapshot_store
                ),
                state=(
                    self._intelligence_state
                ),
            )
        )

        self._telemetry_pipeline.register(
            self._vehicle_health_consumer
        )

        self._driver_statistics_engine = (
            DriverStatisticsEngine(
                score_calculator=(
                    DriverScoreCalculator()
                )
            )
        )

        self._driver_statistics_consumer = (
            DriverStatisticsConsumer(
                engine=(
                    self._driver_statistics_engine
                ),
                state=(
                    self._intelligence_state
                ),
            )
        )

        # --------------------------------------------------------------
        # Fleet intelligence (maintenance + alerts)
        # --------------------------------------------------------------

        self._maintenance_service = (
            MaintenanceService(
                estimators=(
                    EngineEstimator(),
                    BrakeEstimator(),
                    CoolingEstimator(),
                    TransmissionEstimator(),
                    FuelSystemEstimator(),
                )
            )
        )

        self._alert_engine = (
            AlertEngine(
                generators=(
                    HealthAlertsGenerator(),
                    TelemetryAlertsGenerator(),
                    MaintenanceAlertsGenerator(),
                    TripAlertsGenerator(),
                )
            )
        )


        # --------------------------------------------------------------
        # Load fleet configuration
        # --------------------------------------------------------------

        self._configure_fleet()

        self._trip_flush_callback: TripFlushCallback | None = None

        self._initial_fuel_levels: dict[str, float] = {}

        self._running = False

        self._simulation_run_id: str = str(uuid.uuid4())
        self._simulation_start_time: datetime | None = None

    @property
    def run_id(self) -> str:
        return self._simulation_run_id

    @property
    def simulation_run_id(self) -> str:
        return self._simulation_run_id

    @property
    def simulation_start_time(self) -> datetime | None:
        return self._simulation_start_time

    def _configure_fleet(
        self,
    ) -> None:
        """
        Load configured fleet assignments
        and register analytics context.
        """

        configured_fleet = (
            FleetFactory.from_config()
        )

        if self._persistence_service is not None:
            self._fleet_config = configured_fleet

        for assignment in (
            configured_fleet.assignments
        ):

            vehicle = next(
                vehicle
                for vehicle
                in configured_fleet.vehicles
                if (
                    vehicle.vehicle_id
                    == assignment.vehicle_id
                )
            )

            driver = next(
                driver
                for driver
                in configured_fleet.drivers
                if (
                    driver.driver_id
                    == assignment.driver_id
                )
            )

            route = next(
                route
                for route
                in configured_fleet.routes
                if (
                    route.route_id
                    == assignment.route_id
                )
            )

            trip = Trip(
                trip_id=(
                    str(uuid.uuid4())
                ),
                vehicle_id=(
                    vehicle.vehicle_id
                ),
                driver_id=(
                    driver.driver_id
                ),
                route_id=(
                    route.route_id
                ),
            )

            self._context_store.register(
                AnalyticsContext(
                    vehicle_id=(
                        vehicle.vehicle_id
                    ),
                    driver_id=(
                        driver.driver_id
                    ),
                    trip_id=(
                        trip.trip_id
                    ),
                    route_id=(
                        route.route_id
                    ),
                    route_type=(
                        route.route_type
                    ),
                    speed_limit_kmh=(
                        route.speed_limit_kmh
                    ),
                    vehicle_make=(
                        vehicle.make
                    ),
                    vehicle_model=(
                        vehicle.model
                    ),
                    vehicle_year=(
                        vehicle.year
                    ),
                    driver_name=(
                        driver.name
                    ),
                )
            )

            self._fleet.add_assignment(
                assignment=assignment,
                vehicle=vehicle,
                driver=driver,
                route=route,
                trip=trip,
            )

    async def run(
        self,
    ) -> None:
        """
        Run the fleet continuously.

        Every telemetry sample flows through:

            FleetRunner
                ↓
            TelemetryPipeline
                ↓
            AnalyticsEngine
                ↓
            AnalyticsSnapshotStream
        """

        self._running = True

        self._simulation_run_id = str(uuid.uuid4())
        self._simulation_start_time = datetime.now(timezone.utc)
        run_seed = hash(self._simulation_run_id) & 0x7FFFFFFF

        start_time = self._simulation_start_time

        logger.info(
            "Simulation started  "
            "run_id=%s  "
            "start_time=%s",
            self._simulation_run_id,
            start_time.isoformat(),
        )

        # --------------------------------------------------------------
        # Seed per-vehicle randomness for this run
        # --------------------------------------------------------------

        for runner in self._fleet._runners:
            runner.run_seed = run_seed

        # --------------------------------------------------------------
        # Persist reference data (vehicles, drivers, routes)
        # --------------------------------------------------------------

        persistence = self._persistence_service

        if persistence is not None and self._fleet_config is not None:
            for vehicle in self._fleet_config.vehicles:
                await persistence.persist_vehicle(vehicle)
            for driver in self._fleet_config.drivers:
                await persistence.persist_driver(driver)
            for route in self._fleet_config.routes:
                await persistence.persist_route(route)

        # --------------------------------------------------------------
        # Persist trip rows BEFORE starting fleet — DB rows must exist
        # before any telemetry is produced, otherwise persist_telemetry
        # will violate the telemetry_samples_trip_id_fkey constraint.
        # --------------------------------------------------------------

        if persistence is not None:
            for runner in self._fleet._runners:
                await persistence.create_trip(
                    trip_id=runner.trip.trip_id,
                    vehicle_id=runner.vehicle.vehicle_id,
                    driver_id=runner.driver.driver_id,
                    route_id=runner.route.route_id,
                    start_time=start_time,
                )

        # --------------------------------------------------------------
        # Start all trips
        # --------------------------------------------------------------

        self._fleet.start_all(
            now=start_time
        )

        self._initial_fuel_levels = {
            runner.vehicle.vehicle_id: runner.vehicle.fuel_level_percent
            for runner in self._fleet._runners
        }

        logger.info("Beginning telemetry stream...")

        # --------------------------------------------------------------
        # Register persistence as telemetry consumer
        # --------------------------------------------------------------

        class _PersistenceTelemetryConsumer:
            def __init__(
                self,
                svc: PersistenceService,
                engine: AlertEngine,
                state: IntelligenceState,
            ) -> None:
                self._svc = svc
                self._engine = engine
                self._state = state

            def consume(self, sample: TelemetrySample) -> None:
                asyncio.ensure_future(
                    self._svc.persist_telemetry(sample)
                )

                health = self._state.get_health_snapshot(
                    sample.vehicle_id
                )

                if health is not None:
                    asyncio.ensure_future(
                        self._svc.persist_vehicle_health(health)
                    )

                alerts = self._engine.generate_alerts(
                    health_snapshot=health,
                    telemetry=(sample,),
                )

                if alerts:
                    asyncio.ensure_future(
                        self._svc.persist_alerts(alerts)
                    )

        if persistence is not None:
            self._telemetry_pipeline.register(
                _PersistenceTelemetryConsumer(
                    persistence,
                    self._alert_engine,
                    self._intelligence_state,
                )
            )

        # --------------------------------------------------------------
        # Subscribe persistence to analytics snapshot stream
        # --------------------------------------------------------------

        class _PersistenceSnapshotSubscriber:
            def __init__(self, svc: PersistenceService) -> None:
                self._svc = svc
            def publish(self, snapshot: AnalyticsSnapshot) -> None:
                asyncio.ensure_future(
                    self._svc.persist_behaviour_events(snapshot)
                )

        if persistence is not None:
            self._snapshot_stream.subscribe(
                _PersistenceSnapshotSubscriber(persistence)
            )

        # --------------------------------------------------------------
        # Persist trip completion (hooks into existing callback)
        # --------------------------------------------------------------

        if persistence is not None:
            existing_callback = self._trip_flush_callback

            def _persist_trip_completion(
                summary: Any,
                context: Any,
                runtime_state: Any,
                all_events: list,
            ) -> None:
                if existing_callback is not None:
                    existing_callback(
                        summary, context, runtime_state, all_events
                    )

                vehicle_id = summary.vehicle_id
                runner = next(
                    (
                        r
                        for r in self._fleet._runners
                        if r.vehicle.vehicle_id == vehicle_id
                    ),
                    None,
                )

                if runner is None:
                    logger.warning(
                        "No fleet runner found for completed vehicle %s, "
                        "using default values for trip completion",
                        vehicle_id,
                    )
                    asyncio.ensure_future(
                        persistence.complete_trip(
                            trip_id=summary.trip_id,
                            end_time=datetime.now(timezone.utc),
                            distance_km=summary.total_distance_km,
                            duration_seconds=0,
                            fuel_used_liters=0.0,
                            average_speed_kmh=0.0,
                            maximum_speed_kmh=0.0,
                            trip_score=0.0,
                        )
                    )
                    return

                trip_obj = runner.trip

                duration_seconds = 0
                if (
                    trip_obj.started_at is not None
                    and trip_obj.completed_at is not None
                ):
                    duration_seconds = int(
                        (
                            trip_obj.completed_at - trip_obj.started_at
                        ).total_seconds()
                    )

                distance_km = trip_obj.distance_travelled_km

                average_speed_kmh = 0.0
                if duration_seconds > 0:
                    average_speed_kmh = round(
                        distance_km / (duration_seconds / 3600), 2
                    )

                maximum_speed_kmh = (
                    context.speed_limit_kmh
                    + summary.maximum_speed_excess_kmh
                )

                initial_fuel_pct = self._initial_fuel_levels.get(
                    vehicle_id,
                    runner.vehicle.fuel_level_percent,
                )
                final_fuel_pct = runner.vehicle.fuel_level_percent
                fuel_used_pct = initial_fuel_pct - final_fuel_pct
                tank_capacity_liters = 60.0
                fuel_used_liters = round(
                    (fuel_used_pct / 100.0) * tank_capacity_liters, 2
                )

                trip_score = round(
                    _compute_safety_score(summary), 0
                )

                logger.info(
                    "Completing trip %s: "
                    "distance=%.1fkm "
                    "fuel=%.1fL "
                    "avg_speed=%.0fkm/h "
                    "max_speed=%.0fkm/h "
                    "score=%.0f",
                    summary.trip_id,
                    distance_km,
                    fuel_used_liters,
                    average_speed_kmh,
                    maximum_speed_kmh,
                    trip_score,
                )

                asyncio.ensure_future(
                    persistence.complete_trip(
                        trip_id=summary.trip_id,
                        end_time=datetime.now(timezone.utc),
                        distance_km=distance_km,
                        duration_seconds=duration_seconds,
                        fuel_used_liters=fuel_used_liters,
                        average_speed_kmh=average_speed_kmh,
                        maximum_speed_kmh=maximum_speed_kmh,
                        trip_score=trip_score,
                    )
                )

            self._trip_flush_callback = _persist_trip_completion

        now = start_time

        pre_tick_vehicles = {
            runner.vehicle.vehicle_id
            for runner
            in self._fleet.active_runners()
        }

        latest_samples: dict[str, TelemetrySample] = {}

        while (
            self._running
            and self._fleet.active_runners()
        ):

            samples = (
                self._fleet.tick_all(
                    now=now
                )
            )

            for sample in samples:

                latest_samples[
                    sample.vehicle_id
                ] = sample

                self._telemetry_pipeline.publish(
                    sample
                )

            post_tick_vehicles = {
                runner.vehicle.vehicle_id
                for runner
                in self._fleet.active_runners()
            }

            just_completed = (
                pre_tick_vehicles
                - post_tick_vehicles
            )

            for vehicle_id in just_completed:
                all_events = (
                    self._analytics_engine.flush_vehicle(
                        vehicle_id=vehicle_id,
                        timestamp=now,
                    )
                )

                # ------------------------------------------------------
                # Feed the completed trip into driver statistics
                # ------------------------------------------------------

                runner = next(
                    (
                        r
                        for r in self._fleet._runners
                        if r.vehicle.vehicle_id == vehicle_id
                    ),
                    None,
                )

                if runner is not None:
                    statistics = (
                        self._driver_statistics_consumer.record_trip(
                            driver_id=runner.trip.driver_id,
                            behaviour_events=all_events,
                            trip=runner.trip,
                        )
                    )

                    if persistence is not None:
                        asyncio.ensure_future(
                            persistence.persist_driver_statistics(
                                statistics
                            )
                        )

                        health = (
                            self._intelligence_state.get_health_snapshot(
                                vehicle_id
                            )
                        )

                        recommendations = ()
                        records = ()

                        if health is not None:
                            try:
                                recommendations = (
                                    self._maintenance_service
                                    .estimate_maintenance(
                                        health_snapshot=health,
                                        vehicle=runner.vehicle,
                                        telemetry_sample=(
                                            latest_samples.get(
                                                vehicle_id
                                            )
                                        ),
                                        odometer_km=(
                                            runner.vehicle.odometer_km
                                        ),
                                    )
                                )
                                records = (
                                    self._maintenance_service
                                    .build_records(
                                        recommendations=(
                                            recommendations
                                        ),
                                        odometer_km=(
                                            runner.vehicle.odometer_km
                                        ),
                                    )
                                )
                            except Exception:
                                logger.exception(
                                    "Maintenance estimation failed for "
                                    "vehicle %s",
                                    vehicle_id,
                                )
                                recommendations = ()
                                records = ()

                        if records:
                            asyncio.ensure_future(
                                persistence.persist_maintenance_records(
                                    records
                                )
                            )

                        trip_alerts = (
                            self._alert_engine.generate_alerts(
                                recommendations=recommendations,
                                health_snapshot=health,
                                trip=runner.trip,
                                behaviour_events=all_events,
                            )
                        )

                        if trip_alerts:
                            asyncio.ensure_future(
                                persistence.persist_alerts(
                                    trip_alerts
                                )
                            )

                if self._trip_flush_callback is not None:
                    summary = (
                        self._analytics_engine.get_summary(
                            vehicle_id
                        )
                    )
                    context = (
                        self._context_store.get(
                            vehicle_id
                        )
                    )
                    runtime_state = (
                        self._runtime_store.get(
                            vehicle_id
                        )
                    )
                    if (
                        summary is not None
                        and context is not None
                        and runtime_state is not None
                    ):
                        self._trip_flush_callback(
                            summary,
                            context,
                            runtime_state,
                            all_events,
                        )

            pre_tick_vehicles = post_tick_vehicles

            now += timedelta(
                seconds=self._tick_seconds
            )

            await asyncio.sleep(
                self._tick_seconds
            )

        if persistence is not None:
            await persistence.close()

    def stop(
        self,
    ) -> None:

        self._running = False

    @property
    def analytics_engine(
        self,
    ) -> AnalyticsEngine:

        return self._analytics_engine

    @property
    def snapshot_stream(
        self,
    ) -> AnalyticsSnapshotStream:

        return self._snapshot_stream

    @property
    def snapshot_store(
        self,
    ) -> AnalyticsSnapshotStore:

        return self._snapshot_store

    @property
    def telemetry_pipeline(
        self,
    ) -> TelemetryPipeline:

        return self._telemetry_pipeline

    @property
    def fleet(
        self,
    ) -> FleetRunner:

        return self._fleet

    @property
    def dashboard_builder(self):
        return self._dashboard_builder

    @property
    def runtime_store(
        self,
    ) -> RuntimeStateStore:
        return self._runtime_store

    @property
    def context_store(
        self,
    ) -> AnalyticsContextStore:
        return self._context_store

    @property
    def intelligence_state(
        self,
    ) -> IntelligenceState:
        return self._intelligence_state

    @property
    def vehicle_health_engine(
        self,
    ) -> VehicleHealthEngine:
        return self._vehicle_health_engine

    @property
    def vehicle_health_consumer(
        self,
    ) -> VehicleHealthConsumer:
        return self._vehicle_health_consumer

    @property
    def driver_statistics_engine(
        self,
    ) -> DriverStatisticsEngine:
        return self._driver_statistics_engine

    @property
    def driver_statistics_consumer(
        self,
    ) -> DriverStatisticsConsumer:
        return self._driver_statistics_consumer

    @property
    def maintenance_service(
        self,
    ) -> MaintenanceService:
        return self._maintenance_service

    @property
    def alert_engine(
        self,
    ) -> AlertEngine:
        return self._alert_engine

    def set_trip_flush_callback(
        self,
        callback: TripFlushCallback,
    ) -> None:
        self._trip_flush_callback = callback