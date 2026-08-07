"""
Analytics Engine.

Central telemetry consumer that combines live runtime state with
immutable analytics context and coordinates:

    Telemetry
        ↓
    Runtime State
        ↓
    Analysis Input
        ↓
    Driver Behaviour Analysis
        ↓
    Behaviour Events
        ↓
    Trip-Level Behaviour Summary
"""

from datetime import datetime

from backend.analytics.context.context_store import (
    AnalyticsContextStore,
)
from backend.analytics.behaviour.detection.analysis import (
    DriverBehaviourAnalysis,
)
from backend.analytics.behaviour.detection.analyzer import (
    DriverBehaviourAnalyzer,
)
from backend.analytics.behaviour.events.event import (
    BehaviourEvent,
)
from backend.analytics.behaviour.events.tracker import (
    BehaviourEventTracker,
)
from backend.analytics.behaviour.aggregation.summary import (
    DriverBehaviourSummary,
)
from backend.analytics.behaviour.aggregation.summarizer import (
    DriverBehaviourSummarizer,
)
from backend.analytics.input.analysis_input import (
    AnalysisInput,
)
from backend.analytics.state.runtime_state_store import (
    RuntimeStateStore,
)
from backend.telemetry.models.telemetry_sample import (
    TelemetrySample,
)
from backend.analytics.snapshot.analytics_snapshot import (
    AnalyticsSnapshot,
)
from backend.analytics.snapshot.snapshot_store import (
    AnalyticsSnapshotStore,
)
from backend.streaming.snapshot_stream import (
    AnalyticsSnapshotStream,
)


class AnalyticsEngine:
    """
    Central coordinator for the analytics pipeline.

    Responsibilities:

        1. Consume telemetry.
        2. Update runtime analytics state.
        3. Combine runtime state with immutable context.
        4. Run point-in-time driver behaviour analysis.
        5. Track temporal behaviour events.
        6. Store completed events per vehicle.
        7. Generate trip-level behaviour summaries when a vehicle
           finishes its trip.
    """

    def __init__(
        self,
        runtime_store: RuntimeStateStore,
        context_store: AnalyticsContextStore,
        driver_behaviour_analyzer: DriverBehaviourAnalyzer,
        event_tracker: BehaviourEventTracker,
        behaviour_summarizer: DriverBehaviourSummarizer,
        snapshot_store: AnalyticsSnapshotStore,
        snapshot_stream: AnalyticsSnapshotStream,
    ) -> None:
        self._runtime_store = runtime_store
        self._context_store = context_store
        self._driver_behaviour_analyzer = (
            driver_behaviour_analyzer
        )
        self._event_tracker = event_tracker
        self._behaviour_summarizer = (
            behaviour_summarizer
        )
        self._snapshot_stream = (
            snapshot_stream
        )
        self._snapshot_store = snapshot_store

        # Latest AnalysisInput for each vehicle.
        self._latest_inputs: dict[
            str,
            AnalysisInput,
        ] = {}

        # Latest point-in-time behaviour analysis for each vehicle.
        self._latest_behaviour: dict[
            str,
            DriverBehaviourAnalysis,
        ] = {}

        # Completed trip-level summaries keyed by vehicle ID.
        self._summaries: dict[
            str,
            DriverBehaviourSummary,
        ] = {}

        # Completed events are isolated per vehicle.
        #
        # This is important because multiple vehicles may be running
        # simultaneously. Events from vehicle A must never be mixed
        # with events from vehicle B.
        self._completed_events: dict[
            str,
            list[BehaviourEvent],
        ] = {}

    def consume(
        self,
        sample: TelemetrySample,
    ) -> AnalyticsSnapshot:
        """
        Consume telemetry and run the analytics pipeline.
        """

        # --------------------------------------------------------------
        # 1. Update the live runtime state.
        # --------------------------------------------------------------

        runtime_state = self._runtime_store.update(
            sample
        )

        # --------------------------------------------------------------
        # 2. Retrieve immutable analytics context.
        # --------------------------------------------------------------

        context = self._context_store.get(
            sample.vehicle_id
        )

        if context is None:
            raise ValueError(
                f"No analytics context registered for vehicle "
                f"'{sample.vehicle_id}'."
            )

        # --------------------------------------------------------------
        # 3. Build the complete input for analytics.
        # --------------------------------------------------------------

        analysis_input = AnalysisInput(
            runtime_state=runtime_state,
            context=context,
        )

        self._latest_inputs[
            sample.vehicle_id
        ] = analysis_input

        # --------------------------------------------------------------
        # 4. Run point-in-time driver behaviour analysis.
        # --------------------------------------------------------------

        behaviour_analysis = (
            self._driver_behaviour_analyzer.analyze(
                analysis_input
            )
        )

        self._latest_behaviour[
            sample.vehicle_id
        ] = behaviour_analysis

        # --------------------------------------------------------------
        # 5. Convert point-in-time behaviour into temporal events.
        # --------------------------------------------------------------

        completed_events = (
            self._event_tracker.process(
                analysis=behaviour_analysis,
                timestamp=sample.timestamp,
            )
        )

        # --------------------------------------------------------------
        # 6. Store completed events for THIS vehicle only.
        #
        # IMPORTANT:
        # _completed_events is a dictionary, so we cannot call:
        #
        #     self._completed_events.extend(...)
        #
        # Instead, events must be added to the list belonging to the
        # specific vehicle.
        # --------------------------------------------------------------

        if completed_events:
            self._completed_events.setdefault(
                sample.vehicle_id,
                [],
            ).extend(
                completed_events
            )
        snapshot = AnalyticsSnapshot(
            vehicle_id=sample.vehicle_id,
            driver_id=sample.driver_id,
            trip_id=sample.trip_id,
            timestamp=sample.timestamp,
            telemetry=sample,
            behaviour=behaviour_analysis,
            completed_events=tuple(completed_events),
            active_event_types=tuple(
                self._event_tracker.active_event_types(
                    sample.vehicle_id
                )
            ),
        )
        self._snapshot_store.update(
            snapshot
        )
        self._snapshot_stream.publish(
            snapshot
        )


        return snapshot

    def get_input(
        self,
        vehicle_id: str,
    ) -> AnalysisInput | None:
        """
        Return the latest analysis input for a vehicle.
        """

        return self._latest_inputs.get(
            vehicle_id
        )

    def get_behaviour_analysis(
        self,
        vehicle_id: str,
    ) -> DriverBehaviourAnalysis | None:
        """
        Return the latest point-in-time behaviour analysis
        for a vehicle.
        """

        return self._latest_behaviour.get(
            vehicle_id
        )

    def get_snapshot(
        self,
        vehicle_id: str,
    ) -> AnalyticsSnapshot | None:
        """
        Return the latest analytics snapshot for one vehicle.
        """

        return self._snapshot_store.get(
            vehicle_id
        )

    def get_all_snapshots(
        self,
    ) -> tuple[AnalyticsSnapshot, ...]:
        """
        Return the latest analytics snapshot for every vehicle.
        """

        return self._snapshot_store.get_all()

    def drain_completed_events(
        self,
        vehicle_id: str,
    ) -> list[BehaviourEvent]:
        """
        Return completed events for one vehicle and clear them.

        Events belonging to other vehicles remain untouched.
        """

        events = self._completed_events.get(
            vehicle_id,
            [],
        )

        self._completed_events[
            vehicle_id
        ] = []

        return events

    def flush_vehicle(
        self,
        vehicle_id: str,
        timestamp: datetime,
        *,
        total_distance_km: float | None = None,
    ) -> list[BehaviourEvent]:
        """
        Flush active behaviour events for one vehicle.

        Called when that vehicle's trip ends.

        ``total_distance_km`` must be the completed trip's distance,
        not the vehicle's lifetime odometer, so the behaviour summary
        (and any safety scoring derived from it) reflects the trip
        only.

        Events from other vehicles remain active and are not affected.
        """

        # --------------------------------------------------------------
        # 1. Close any continuous events that are still active.
        #
        # Example:
        #
        # Vehicle V-101 is still speeding when its trip ends.
        #
        # The tracker has not yet seen a "speeding = False" sample,
        # so we explicitly close that event here.
        # --------------------------------------------------------------

        flushed_events = (
            self._event_tracker.flush_vehicle(
                vehicle_id=vehicle_id,
                timestamp=timestamp,
            )
        )

        # --------------------------------------------------------------
        # 2. Retrieve events that were already completed earlier.
        # --------------------------------------------------------------

        completed_events = (
            self._completed_events.get(
                vehicle_id,
                [],
            )
        )

        # --------------------------------------------------------------
        # 3. Combine both types of events:
        #
        #     previously completed events
        #     +
        #     events closed during the flush
        # --------------------------------------------------------------

        all_events = (
            completed_events
            + flushed_events
        )

        # --------------------------------------------------------------
        # 4. Clear the vehicle's event queue.
        #
        # This prevents the same events from being included in a
        # future summary again.
        # --------------------------------------------------------------

        self._completed_events[
            vehicle_id
        ] = []

        # --------------------------------------------------------------
        # 5. Generate the trip-level behaviour summary.
        # --------------------------------------------------------------

        analysis_input = (
            self._latest_inputs.get(
                vehicle_id
            )
        )

        if analysis_input is not None:

            context = (
                analysis_input.context
            )

            # ----------------------------------------------------------
            # Build the trip summary from the completed trip's distance.
            #
            # The lifetime odometer is intentionally NOT used here: a
            # vehicle's total odometer is a lifetime value and would
            # break every distance-normalised metric (average speed,
            # fuel, safety density) for a single trip.
            # ----------------------------------------------------------

            summary = (
                self._behaviour_summarizer.summarize(
                    vehicle_id=vehicle_id,
                    driver_id=context.driver_id,
                    trip_id=context.trip_id,
                    total_distance_km=(
                        total_distance_km
                        if total_distance_km is not None
                        else 0.0
                    ),
                    events=all_events,
                )
            )

            self._summaries[
                vehicle_id
            ] = summary

        return all_events

    def get_summary(
        self,
        vehicle_id: str,
    ) -> DriverBehaviourSummary | None:
        """
        Return the latest completed behaviour summary
        for a vehicle.
        """

        return self._summaries.get(
            vehicle_id
        )

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