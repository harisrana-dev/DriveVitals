"""
VehicleHealthConsumer.

Application consumer that bridges the existing TelemetryPipeline into
the VehicleHealthEngine. For every TelemetrySample it pairs the sample
with the current AnalyticsSnapshot (produced by the AnalyticsEngine)
and stores the resulting HealthSnapshot in the IntelligenceState.
"""

import logging

from backend.analytics.snapshot.snapshot_store import (
    AnalyticsSnapshotStore,
)
from backend.analytics.vehicle_health.models.health_snapshot import (
    HealthSnapshot,
)
from backend.analytics.vehicle_health.vehicle_health_engine import (
    VehicleHealthEngine,
)
from backend.application.intelligence_state import (
    IntelligenceState,
)
from backend.telemetry.models.telemetry_sample import (
    TelemetrySample,
)

logger = logging.getLogger(__name__)


class VehicleHealthConsumer:
    """
    Purpose:
        Route telemetry into the VehicleHealthEngine and retain the
        latest HealthSnapshot per vehicle.
    Inputs:
        TelemetrySample via the TelemetryPipeline.
    Outputs:
        Latest HealthSnapshot per vehicle in the IntelligenceState.
    """

    def __init__(
        self,
        *,
        engine: VehicleHealthEngine,
        snapshot_store: AnalyticsSnapshotStore,
        state: IntelligenceState,
    ) -> None:
        self._engine = engine
        self._snapshot_store = snapshot_store
        self._state = state

    def consume(
        self,
        sample: TelemetrySample,
    ) -> None:
        """
        Analyze vehicle health for one telemetry observation.
        """

        snapshot = self._snapshot_store.get(
            sample.vehicle_id
        )

        if snapshot is None:
            logger.debug(
                "No analytics snapshot yet for vehicle %s, "
                "skipping health analysis",
                sample.vehicle_id,
            )
            return

        health_snapshot = (
            self._engine.analyze(
                sample=sample,
                snapshot=snapshot,
            )
        )

        self._state.update_health_snapshot(
            health_snapshot
        )

    def get_latest(
        self,
        vehicle_id: str,
    ) -> HealthSnapshot | None:
        """
        Return the latest HealthSnapshot for one vehicle.
        """

        return self._state.get_health_snapshot(
            vehicle_id
        )
