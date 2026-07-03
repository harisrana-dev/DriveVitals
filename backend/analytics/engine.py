"""
DriveVitals Analytics Engine (SAFE VERSION)

This version prevents startup crashes by making
all analyzers optional.
"""

from telemetry.models import TelemetryPacket
from analytics.rule_engine import RuleEngine


class AnalyticsEngine:

    def __init__(self):

        self.rule_engine = RuleEngine()

        # safe optional loading
        self.driver_behaviour = None
        self.vehicle_health = None
        self.fuel_efficiency = None
        self.trip_performance = None

        # try loading analyzers safely
        try:
            from analytics.driver_behaviour import DriverBehaviourAnalyzer
            self.driver_behaviour = DriverBehaviourAnalyzer()
        except Exception:
            print("⚠️ driver_behaviour not loaded")

        try:
            from analytics.vehicle_health import VehicleHealthAnalyzer
            self.vehicle_health = VehicleHealthAnalyzer()
        except Exception:
            print("⚠️ vehicle_health not loaded")

        try:
            from analytics.fuel_efficiency import FuelEfficiencyAnalyzer
            self.fuel_efficiency = FuelEfficiencyAnalyzer()
        except Exception:
            print("⚠️ fuel_efficiency not loaded")

        try:
            from analytics.trip_performance import TripPerformanceAnalyzer
            self.trip_performance = TripPerformanceAnalyzer()
        except Exception:
            print("⚠️ trip_performance not loaded")

    def process(self, packet: TelemetryPacket):

        rule_results = self.rule_engine.evaluate(packet)

        results = {
            "vehicle_id": packet.vehicle_id,
            "timestamp": packet.timestamp,
            "rules": rule_results,
        }

        if self.driver_behaviour:
            results["driver_behaviour"] = self.driver_behaviour.analyze(packet, rule_results)

        if self.vehicle_health:
            results["vehicle_health"] = self.vehicle_health.analyze(packet, rule_results)

        if self.fuel_efficiency:
            results["fuel_efficiency"] = self.fuel_efficiency.analyze(packet, rule_results)

        if self.trip_performance:
            results["trip_performance"] = self.trip_performance.analyze(packet, rule_results)

        return results