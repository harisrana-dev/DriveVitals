"""
DriveVitals Analytics Engine

Coordinates all analytics modules and updates the
Vehicle State Manager with the latest live state.

The Analytics Engine acts as the central orchestration
layer between telemetry processing and live dashboard state.
"""

from telemetry.models import TelemetryPacket
from analytics.rule_engine import RuleEngine

# Global live state manager
from state.state_manager import state_manager


class AnalyticsEngine:

    def __init__(self):

        self.rule_engine = RuleEngine()

        # Shared live vehicle state
        self.state_manager = state_manager

        # Optional analyzers
        self.driver_behaviour = None
        self.vehicle_health = None
        self.fuel_efficiency = None
        self.trip_performance = None

        # -----------------------------
        # Safe loading of analyzers
        # -----------------------------

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

    # --------------------------------------------------

    def process(self, packet: TelemetryPacket):
        print(f"Processing {packet.vehicle_id}")
        

        # Evaluate engineering rules
        rule_results = self.rule_engine.evaluate(packet)

        analytics_results = {
            "vehicle_id": packet.vehicle_id,
            "timestamp": packet.timestamp,
            "rules": rule_results,
        }

        # Driver Behaviour
        if self.driver_behaviour:
            analytics_results["driver_behaviour"] = (
                self.driver_behaviour.analyze(
                    packet,
                    rule_results
                )
            )

        # Vehicle Health
        if self.vehicle_health:
            analytics_results["vehicle_health"] = (
                self.vehicle_health.analyze(
                    packet,
                    rule_results
                )
            )

        # Fuel Efficiency
        if self.fuel_efficiency:
            analytics_results["fuel_efficiency"] = (
                self.fuel_efficiency.analyze(
                    packet,
                    rule_results
                )
            )

        # Trip Performance
        if self.trip_performance:
            analytics_results["trip_performance"] = (
                self.trip_performance.analyze(
                    packet,
                    rule_results
                )
            )

        # ---------------------------------------
        # Update the live Vehicle State Manager
        # ---------------------------------------

        self.state_manager.update_state(
            packet,
             analytics_results
        )

        return analytics_results