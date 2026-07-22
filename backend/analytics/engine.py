"""AnalyticsEngine: central orchestration for the analytics pipeline.

Flow:
    TelemetryPacket + PhysicsTickResult + Trip context
        -> AnalyticsInput.from_packet()
        -> RuleEngine.evaluate()
        -> EventManager (lifecycle tracking)
        -> Individual analyzers
        -> Structured analytics results

The engine is deterministic, testable, and does not depend on
old V1 packet fields or the state manager.
"""

from __future__ import annotations

from analytics.analytics_input import AnalyticsInput
from analytics.driver_behaviour import DriverBehaviourAnalyzer
from analytics.driver_ranking import DriverRankingAnalyzer
from analytics.event_manager import EventManager
from analytics.fleet_trends import FleetTrendAnalyzer
from analytics.fuel_efficiency import FuelEfficiencyAnalyzer
from analytics.maintenance_queue import MaintenanceQueueAnalyzer
from analytics.rule_engine import RuleEngine
from analytics.trip_performance import TripPerformanceAnalyzer
from analytics.vehicle_health import VehicleHealthAnalyzer
from digital_twin.telemetry.telemetry_packet import TelemetryPacket


class AnalyticsEngine:
    """Orchestrates all analytics modules against incoming telemetry."""

    def __init__(self) -> None:
        self.rule_engine = RuleEngine()
        self.event_manager = EventManager()
        self.driver_behaviour = DriverBehaviourAnalyzer()
        self.vehicle_health = VehicleHealthAnalyzer()
        self.fuel_efficiency = FuelEfficiencyAnalyzer()
        self.trip_performance = TripPerformanceAnalyzer()
        self.driver_ranking = DriverRankingAnalyzer()
        self.maintenance_queue = MaintenanceQueueAnalyzer()
        self.fleet_trends = FleetTrendAnalyzer()

        #: Per-vehicle AnalyticsInput history for fleet trends.
        self._latest_inputs: dict[str, AnalyticsInput] = {}
        #: Per-vehicle driver safety scores for cumulative ranking.
        self._vehicle_scores: dict[str, int] = {}

    def process(
        self,
        packet: TelemetryPacket,
        physics_result: object | None = None,
        trip: object | None = None,
    ) -> dict:
        """Process one tick through the full analytics pipeline.

        Args:
            packet: An immutable TelemetryPacket from the Digital Twin.
            physics_result: Optional PhysicsTickResult with per-tick
                distance and fuel consumption metrics.
            trip: Optional Trip entity with trip progress data.

        Returns:
            Structured analytics results dict.
        """
        # 1. Convert to analytics boundary (with physics + trip context)
        analytics_input = AnalyticsInput.from_packet(
            packet, physics_result=physics_result, trip=trip,
        )

        # 2. Run rule engine
        raw_events = self.rule_engine.evaluate(analytics_input)

        # 3. Update event lifecycle
        active_keys = {(e.vehicle_id, e.event) for e in raw_events}
        snapshots = {}
        for e in raw_events:
            key = (e.vehicle_id, e.event)
            snapshots[key] = {
                "rule_id": e.rule_id,
                "category": e.category,
                "severity": e.severity,
                "value": e.value,
                "threshold": e.threshold,
                "timestamp": e.timestamp,
            }
        self.event_manager.update(active_keys, snapshots, analytics_input.tick_id)

        # Build event dicts for the result
        active_events = self.event_manager.get_active_events()
        event_dicts = [e.to_dict() for e in active_events]

        # 4. Track latest input per vehicle for fleet trends
        self._latest_inputs[analytics_input.vehicle_id] = analytics_input

        # 5. Run individual analyzers
        driver_behaviour = self.driver_behaviour.analyze(
            analytics_input, raw_events,
        )

        vehicle_health = self.vehicle_health.analyze(
            analytics_input, raw_events,
        )

        fuel_efficiency = self.fuel_efficiency.analyze(
            analytics_input, raw_events,
        )

        trip_performance = self.trip_performance.analyze(
            analytics_input, raw_events,
        )

        # 6. Driver ranking (cumulative per vehicle)
        vid = analytics_input.vehicle_id
        current_score = self._vehicle_scores.get(vid, 100)
        driver_ranking = self.driver_ranking.analyze(
            analytics_input, raw_events, current_score=current_score,
        )
        self._vehicle_scores[vid] = driver_ranking["score"]

        # 7. Maintenance queue
        maintenance_queue = self.maintenance_queue.analyze(
            analytics_input,
            {"vehicle_health": vehicle_health, "fuel_efficiency": fuel_efficiency},
        )

        # 8. Fleet trends
        fleet_trends = self.fleet_trends.update(self._latest_inputs)

        return {
            "vehicle_id": analytics_input.vehicle_id,
            "tick_id": analytics_input.tick_id,
            "timestamp": analytics_input.timestamp,
            "events": event_dicts,
            "driver_behaviour": driver_behaviour,
            "vehicle_health": vehicle_health,
            "fuel_efficiency": fuel_efficiency,
            "trip_performance": trip_performance,
            "driver_ranking": driver_ranking,
            "maintenance_queue": maintenance_queue,
            "fleet_trends": fleet_trends,
        }
