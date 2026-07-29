from backend.analytics.snapshot.analytics_snapshot import (
    AnalyticsSnapshot,
)

from backend.analytics.context.context_store import (
    AnalyticsContextStore,
)

from backend.dashboard.schemas.dashboard_payload import (
    DashboardSnapshot,
    VehicleDashboardSummary,
)


_ALERT_LABELS = {
    "speeding": "Speed limit exceeded",
    "harsh_braking": "Harsh braking detected",
    "aggressive_throttle": "Aggressive acceleration",
    "high_rpm": "High RPM operation",
}


class DashboardBuilder:

    def __init__(
        self,
        context_store: AnalyticsContextStore,
    ) -> None:
        self._context_store = context_store
        self._latest = {}

    def update(
        self,
        snapshot: AnalyticsSnapshot,
    ) -> DashboardSnapshot:

        telemetry = snapshot.telemetry

        context = self._context_store.get(
            snapshot.vehicle_id
        )

        vehicle_name = None
        driver_name = None

        if context is not None:
            vehicle_name = (
                f"{context.vehicle_year} "
                f"{context.vehicle_make} "
                f"{context.vehicle_model}"
            )
            driver_name = (
                context.driver_name or None
            )

        health_score = self._compute_health(
            telemetry.speed_kmh,
            telemetry.coolant_temperature_c,
            telemetry.fuel_level_percent,
            telemetry.engine_load_percent,
            snapshot.active_event_types,
        )

        driver_safety_score = self._compute_driver_safety(
            snapshot.active_event_types,
        )

        driver_risk_level = self._compute_risk_level(
            driver_safety_score,
        )

        alert_texts = [
            _ALERT_LABELS.get(evt, evt)
            for evt in snapshot.active_event_types
        ]
        active_alert_text = (
            alert_texts[0] if alert_texts else None
        )

        status = self._calculate_status(
            telemetry.speed_kmh,
        )

        vehicle = VehicleDashboardSummary(
            vehicle_id=snapshot.vehicle_id,
            driver_id=snapshot.driver_id,
            vehicle_name=vehicle_name,
            driver_name=driver_name,
            operational_status=status,
            speed_kmh=telemetry.speed_kmh,
            rpm=telemetry.rpm,
            throttle_position_percent=(
                telemetry.throttle_position_percent
            ),
            brake_pressure=telemetry.brake_pressure,
            fuel_level_percent=(
                telemetry.fuel_level_percent
            ),
            coolant_temperature_c=(
                telemetry.coolant_temperature_c
            ),
            engine_load_percent=(
                telemetry.engine_load_percent
            ),
            overall_health_score=health_score,
            driver_safety_score=driver_safety_score,
            driver_risk_level=driver_risk_level,
            active_alert_count=len(
                snapshot.active_event_types
            ),
            active_alert_text=active_alert_text,
            active_event_types=snapshot.active_event_types,
            speeding=snapshot.behaviour.speeding,
            aggressive_throttle=(
                snapshot.behaviour.aggressive_throttle
            ),
            harsh_braking=snapshot.behaviour.harsh_braking,
            high_rpm=snapshot.behaviour.high_rpm,
            odometer_km=telemetry.odometer_km,
            last_updated_at=snapshot.timestamp,
        )

        self._latest[
            snapshot.vehicle_id
        ] = vehicle

        vehicles = tuple(self._latest.values())

        health_scores = [
            v.overall_health_score
            for v in vehicles
            if v.overall_health_score is not None
        ]

        fleet_health_score = (
            round(
                sum(health_scores) / len(health_scores),
                1,
            )
            if health_scores
            else 0.0
        )

        attention_required = sum(
            1
            for v in vehicles
            if v.active_alert_count > 0
        )

        return DashboardSnapshot(
            timestamp=snapshot.timestamp,
            total_fleet=len(vehicles),
            active_vehicle_count=sum(
                1
                for v in vehicles
                if v.operational_status == "ACTIVE"
            ),
            fleet_health_score=fleet_health_score,
            attention_required=attention_required,
            vehicles=vehicles,
        )

    @staticmethod
    def _calculate_status(
        speed_kmh: float,
    ) -> str:
        if speed_kmh <= 0:
            return "IDLE"
        return "ACTIVE"

    @staticmethod
    def _compute_health(
        speed_kmh: float,
        coolant_temp: float,
        fuel_level: float,
        engine_load: float,
        active_events: tuple[str, ...],
    ) -> float:
        score = 100.0

        if coolant_temp > 105:
            score -= 25
        elif coolant_temp > 95:
            score -= 10

        if fuel_level < 15:
            score -= 20
        elif fuel_level < 30:
            score -= 8

        if engine_load > 85:
            score -= 10

        score -= len(active_events) * 8

        return max(0.0, min(100.0, round(score, 1)))

    @staticmethod
    def _compute_driver_safety(
        active_events: tuple[str, ...],
    ) -> float:
        score = 100.0
        score -= len(active_events) * 12
        if "speeding" in active_events:
            score -= 8
        if "harsh_braking" in active_events:
            score -= 10
        if "aggressive_throttle" in active_events:
            score -= 6
        if "high_rpm" in active_events:
            score -= 6
        return max(0.0, min(100.0, round(score, 1)))

    @staticmethod
    def _compute_risk_level(
        driver_safety_score: float,
    ) -> str:
        if driver_safety_score >= 90:
            return "low"
        if driver_safety_score >= 70:
            return "moderate"
        if driver_safety_score >= 50:
            return "high"
        return "critical"
