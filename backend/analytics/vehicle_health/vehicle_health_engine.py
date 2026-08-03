"""
Vehicle Health Engine.

Coordinates the subsystem health analyzers and produces a HealthSnapshot
for every telemetry observation. The engine owns orchestration and the
per-vehicle telemetry window only — all scoring decisions belong to the
dedicated analyzers.

    Telemetry + AnalyticsSnapshot
                ↓
          Subsystem Analyzers
                ↓
          HealthSnapshot
"""

import logging
from collections import deque
from collections.abc import Mapping, Sequence
from datetime import datetime

from backend.analytics.snapshot.analytics_snapshot import AnalyticsSnapshot
from backend.analytics.vehicle_health.analyzers import (
    SubsystemHealthAnalyzer,
)
from backend.analytics.vehicle_health.health_config import (
    DEFAULT_HEALTH_CONFIG,
    HealthConfig,
    clamp_score,
    status_for_score,
)
from backend.analytics.vehicle_health.models.health_snapshot import (
    HealthSnapshot,
)
from backend.analytics.vehicle_health.models.subsystem_health import (
    HealthStatus,
    Subsystem,
    SubsystemHealth,
)
from backend.telemetry.models.telemetry_sample import TelemetrySample

logger = logging.getLogger(__name__)


class VehicleHealthEngine:
    """
    Purpose:
        Orchestrate subsystem analyzers into a single HealthSnapshot.
    Inputs:
        One TelemetrySample plus its AnalyticsSnapshot.
    Outputs:
        A HealthSnapshot for one vehicle.
    """

    def __init__(
        self,
        *,
        analyzers: Sequence[SubsystemHealthAnalyzer],
        config: HealthConfig | None = None,
    ) -> None:
        if not analyzers:
            raise ValueError("at least one subsystem analyzer is required")

        subsystems = [analyzer.subsystem for analyzer in analyzers]
        if len(set(subsystems)) != len(subsystems):
            raise ValueError(
                "each analyzer must evaluate a distinct subsystem"
            )

        self._config = config if config is not None else DEFAULT_HEALTH_CONFIG
        self._validate_config(self._config)
        self._analyzers = tuple(analyzers)
        self._windows: dict[str, deque[TelemetrySample]] = {}

    @staticmethod
    def _validate_config(config: HealthConfig) -> None:
        if config.window_size < 1:
            raise ValueError("config.window_size must be at least 1")

        weights = config.weights
        if not weights:
            raise ValueError("config.weights must not be empty")
        if any(weight < 0.0 for weight in weights.values()):
            raise ValueError("config.weights must be non-negative")
        if sum(weights.values()) <= 0.0:
            raise ValueError("config.weights must sum to a positive value")

    def analyze(
        self,
        *,
        sample: TelemetrySample,
        snapshot: AnalyticsSnapshot,
    ) -> HealthSnapshot:
        """
        Evaluate vehicle health for one telemetry observation.
        """
        if sample.vehicle_id != snapshot.vehicle_id:
            raise ValueError(
                "sample and snapshot belong to different vehicles "
                f"('{sample.vehicle_id}' vs '{snapshot.vehicle_id}')"
            )

        window = self._push_window(sample)

        subsystem_healths: dict[Subsystem, SubsystemHealth] = {}
        for analyzer in self._analyzers:
            health = analyzer.analyze(samples=window, snapshot=snapshot)
            subsystem_healths[health.subsystem] = health

        health_snapshot = self.generate_snapshot(
            vehicle_id=sample.vehicle_id,
            timestamp=sample.timestamp,
            subsystem_healths=subsystem_healths,
            driver_id=snapshot.driver_id,
            trip_id=snapshot.trip_id,
        )

        self._log(health_snapshot)
        return health_snapshot

    def generate_snapshot(
        self,
        *,
        vehicle_id: str,
        timestamp: datetime,
        subsystem_healths: Mapping[Subsystem, SubsystemHealth],
        driver_id: str | None = None,
        trip_id: str | None = None,
    ) -> HealthSnapshot:
        """
        Assemble a HealthSnapshot from per-subsystem results.

        The overall score is the weighted average of the subsystem
        scores using the centralized weights.
        """
        weights = self._config.weights
        total_weight = sum(weights.values())

        overall = sum(
            weights.get(subsystem, 0.0) * health.score
            for subsystem, health in subsystem_healths.items()
        )
        overall_score = clamp_score(overall / total_weight)

        return HealthSnapshot(
            vehicle_id=vehicle_id,
            timestamp=timestamp,
            overall_health_score=overall_score,
            overall_status=status_for_score(
                overall_score,
                self._config.status,
            ),
            engine_health=subsystem_healths[Subsystem.ENGINE],
            cooling_health=subsystem_healths[Subsystem.COOLING],
            transmission_health=subsystem_healths[Subsystem.TRANSMISSION],
            brake_health=subsystem_healths[Subsystem.BRAKES],
            fuel_system_health=subsystem_healths[Subsystem.FUEL_SYSTEM],
            driver_id=driver_id,
            trip_id=trip_id,
        )

    def flush_vehicle(self, vehicle_id: str) -> None:
        """
        Drop all retained state for one vehicle (e.g. on trip end).
        """
        self._windows.pop(vehicle_id, None)

    def _push_window(
        self,
        sample: TelemetrySample,
    ) -> tuple[TelemetrySample, ...]:
        window = self._windows.setdefault(
            sample.vehicle_id,
            deque(maxlen=self._config.window_size),
        )
        window.append(sample)
        return tuple(window)

    @staticmethod
    def _log(health_snapshot: HealthSnapshot) -> None:
        logger.debug(
            "health snapshot for vehicle %s: overall %.1f (%s)",
            health_snapshot.vehicle_id,
            health_snapshot.overall_health_score,
            health_snapshot.overall_status.value,
        )
        if health_snapshot.overall_status is HealthStatus.CRITICAL:
            logger.warning(
                "critical health for vehicle %s: overall %.1f",
                health_snapshot.vehicle_id,
                health_snapshot.overall_health_score,
            )

    @property
    def analyzers(self) -> tuple[SubsystemHealthAnalyzer, ...]:
        """Analyzers registered with this engine."""
        return self._analyzers

    @property
    def config(self) -> HealthConfig:
        """Configuration used by this engine."""
        return self._config
