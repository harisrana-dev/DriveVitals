from backend.analytics.behaviour.detection.analysis import (
    DriverBehaviourAnalysis,
)
from backend.analytics.input.analysis_input import AnalysisInput


class DriverBehaviourAnalyzer:
    """
    Analyzes the current driving behaviour of a vehicle.

    The analyzer combines:

        RuntimeAnalyticsState
            What is happening now?

        AnalyticsContext
            What conditions apply?

    It produces a point-in-time behaviour analysis.
    """

    def __init__(
        self,
        *,
        harsh_braking_threshold: float = 0.75,
        aggressive_throttle_threshold: float = 80.0,
        high_rpm_threshold: float = 4000.0,
    ) -> None:
        self._harsh_braking_threshold = harsh_braking_threshold
        self._aggressive_throttle_threshold = aggressive_throttle_threshold
        self._high_rpm_threshold = high_rpm_threshold

    def analyze(
        self,
        analysis_input: AnalysisInput,
    ) -> DriverBehaviourAnalysis:
        state = analysis_input.runtime_state
        context = analysis_input.context

        speed_excess_kmh = max(
            0.0,
            state.speed_kmh - context.speed_limit_kmh,
        )

        speeding = speed_excess_kmh > 0.0

        harsh_braking = (
            state.brake_pressure >= self._harsh_braking_threshold
            and state.speed_kmh >= 20.0
        )

        aggressive_throttle = (
            state.throttle_position_percent
            >= self._aggressive_throttle_threshold
        )

        high_rpm = state.rpm >= self._high_rpm_threshold

        severity = self._determine_severity(
            speeding=speeding,
            speed_excess_kmh=speed_excess_kmh,
            harsh_braking=harsh_braking,
            aggressive_throttle=aggressive_throttle,
            high_rpm=high_rpm,
        )

        return DriverBehaviourAnalysis(
            vehicle_id=state.vehicle_id,
            driver_id=state.driver_id,
            trip_id=state.trip_id,
            speeding=speeding,
            speed_excess_kmh=speed_excess_kmh,
            harsh_braking=harsh_braking,
            aggressive_throttle=aggressive_throttle,
            high_rpm=high_rpm,
            severity=severity,
            odometer_km=state.odometer_km,
        )

    @staticmethod
    def _determine_severity(
        *,
        speeding: bool,
        speed_excess_kmh: float,
        harsh_braking: bool,
        aggressive_throttle: bool,
        high_rpm: bool,
    ) -> str:
        severe_events = sum(
            [
                harsh_braking,
                speed_excess_kmh >= 20.0,
            ]
        )

        moderate_events = sum(
            [
                speeding,
                aggressive_throttle,
                high_rpm,
            ]
        )

        if severe_events >= 1:
            return "severe"

        if moderate_events >= 2:
            return "moderate"

        if moderate_events == 1:
            return "minor"

        return "normal"