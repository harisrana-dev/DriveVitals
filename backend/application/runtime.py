import asyncio

from datetime import (
    datetime,
    timedelta,
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

from backend.analytics.engine import (
    AnalyticsEngine,
)

from backend.analytics.snapshot.snapshot_store import (
    AnalyticsSnapshotStore,
)

from backend.analytics.state.runtime_state_store import (
    RuntimeStateStore,
)

from backend.fleet.config.fleet_factory import (
    FleetFactory,
)

from backend.fleet.models.trip import (
    Trip,
)

from backend.fleet.runtime.fleet_runner import (
    FleetRunner,
)

from backend.pipeline.telemetry_pipeline import (
    TelemetryPipeline,
)

from backend.streaming.snapshot_stream import (
    AnalyticsSnapshotStream,
)


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
    ) -> None:

        self._tick_seconds = (
            tick_seconds
        )

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
        # Load fleet configuration
        # --------------------------------------------------------------

        self._configure_fleet()

        self._running = False

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
                    f"T-{assignment.assignment_id}"
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

        start_time = datetime.utcnow()

        self._fleet.start_all(
            now=start_time
        )

        now = start_time

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

                self._telemetry_pipeline.publish(
                    sample
                )

            now += timedelta(
                seconds=self._tick_seconds
            )

            await asyncio.sleep(
                self._tick_seconds
            )

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