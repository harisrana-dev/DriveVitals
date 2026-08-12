from backend.analytics.snapshot.analytics_snapshot import (
    AnalyticsSnapshot,
)

from backend.analytics.context.context_store import (
    AnalyticsContextStore,
)

from backend.analytics.vehicle_health.health_reasons import (
    flatten_health_reasons,
)

from backend.dashboard.schemas.dashboard_payload import (
    DashboardSnapshot,
    VehicleDashboardSummary,
)

_TANK_CAPACITY_LITERS = 60.0


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
        trip_provider=None,
        health_provider=None,
    ) -> None:
        self._context_store = context_store
        self._trip_provider = trip_provider
        self._health_provider = health_provider
        self._latest = {}
        self._start_fuel: dict[str, float] = {}

    def _trip_for(
        self,
        vehicle_id: str,
    ):
        if self._trip_provider is None:
            return None
        try:
            return self._trip_provider(vehicle_id)
        except Exception:
            return None

    def _health_for(
        self,
        vehicle_id: str,
    ):
        """
        Fetch the canonical health snapshot computed by the vehicle
        health engine.

        This is the single source of truth for health scores and
        statuses on the live dashboard. Returns None when the health
        provider is unavailable or a snapshot has not been generated
        yet (e.g. a vehicle has not been through the health pipeline).
        """
        if self._health_provider is None:
            return None
        try:
            return self._health_provider(vehicle_id)
        except Exception:
            return None

    @staticmethod
    def _subsystem_health(
        health,
        attribute: str,
    ):
        if health is None:
            return None, None
        subsystem = getattr(health, attribute, None)
        if subsystem is None:
            return None, None
        status = getattr(subsystem.status, "value", subsystem.status)
        return subsystem.score, status

    @staticmethod
    def _trip_distance(
        trip,
        odometer_km: float,
    ) -> float | None:
        if trip is None:
            return None
        if trip.starting_odometer_km is None:
            return None
        if odometer_km is None:
            return None
        return max(0.0, odometer_km - trip.starting_odometer_km)

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

        health = self._health_for(
            snapshot.vehicle_id
        )

        (
            engine_score,
            engine_status,
        ) = self._subsystem_health(
            health,
            "engine_health",
        )
        (
            cooling_score,
            cooling_status,
        ) = self._subsystem_health(
            health,
            "cooling_health",
        )
        (
            brake_score,
            brake_status,
        ) = self._subsystem_health(
            health,
            "brake_health",
        )
        (
            transmission_score,
            transmission_status,
        ) = self._subsystem_health(
            health,
            "transmission_health",
        )
        (
            fuel_system_score,
            fuel_system_status,
        ) = self._subsystem_health(
            health,
            "fuel_system_health",
        )

        health_reasons = flatten_health_reasons(health)

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

        trip = self._trip_for(snapshot.vehicle_id)

        if snapshot.vehicle_id not in self._start_fuel:
            self._start_fuel[snapshot.vehicle_id] = (
                telemetry.fuel_level_percent
            )

        start_fuel = self._start_fuel.get(snapshot.vehicle_id)
        fuel_used_liters = None
        if (
            start_fuel is not None
            and telemetry.fuel_level_percent is not None
        ):
            fuel_used_liters = round(
                max(
                    0.0,
                    (start_fuel - telemetry.fuel_level_percent)
                    / 100.0
                    * _TANK_CAPACITY_LITERS,
                ),
                2,
            )

        route_id = (
            trip.route_id
            if trip is not None
            else context.route_id if context is not None else None
        )

        vehicle = VehicleDashboardSummary(
            vehicle_id=snapshot.vehicle_id,
            driver_id=snapshot.driver_id,
            vehicle_name=vehicle_name,
            driver_name=driver_name,
            operational_status=status,
            trip_status="active",
            speed_kmh=telemetry.speed_kmh,
            rpm=telemetry.rpm,
            throttle_position_percent=(
                telemetry.throttle_position_percent
            ),
            brake_percent=(
                round(telemetry.brake_pressure * 100.0, 2)
                if telemetry.brake_pressure is not None
                else None
            ),
            fuel_level_percent=(
                telemetry.fuel_level_percent
            ),
            coolant_temperature_c=(
                telemetry.coolant_temperature_c
            ),
            engine_load_percent=(
                telemetry.engine_load_percent
            ),
            overall_health_score=(
                health.overall_health_score
                if health is not None
                else None
            ),
            overall_health_status=(
                health.overall_status.value
                if health is not None
                else None
            ),
            engine_health=engine_score,
            cooling_health=cooling_score,
            brake_health=brake_score,
            transmission_health=transmission_score,
            fuel_system_health=fuel_system_score,
            engine_health_status=engine_status,
            cooling_health_status=cooling_status,
            brake_health_status=brake_status,
            transmission_health_status=transmission_status,
            fuel_system_health_status=fuel_system_status,
            health_reasons=health_reasons,
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
            route_id=route_id,
            route_name=(
                (context.route_name or None)
                if context is not None
                else None
            ),
            trip_started_at=(
                trip.started_at
                if trip is not None
                else None
            ),
            trip_distance_km=self._trip_distance(
                trip,
                telemetry.odometer_km,
            ),
            fuel_rate_lph=telemetry.fuel_rate_lph,
            fuel_used_liters=fuel_used_liters,
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
            else None
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

    def mark_trip_completed(
        self,
        vehicle_id: str,
        completed_at,
    ) -> DashboardSnapshot | None:
        """
        Surface a completed trip lifecycle state for one vehicle.

        Runtime synchronization only: no analytics are computed here.
        The cached summary for the vehicle is re-labelled as
        TRIP COMPLETED (stationary) so the frontend can render the
        ACTIVE -> TRIP COMPLETED -> OFFLINE lifecycle. Returns a fresh
        snapshot for the current fleet, or None if the vehicle has not
        been seen by the builder yet.
        """

        vehicle = self._latest.get(vehicle_id)

        if vehicle is None:
            return None

        self._start_fuel.pop(vehicle_id, None)

        completed = VehicleDashboardSummary(
            vehicle_id=vehicle.vehicle_id,
            driver_id=vehicle.driver_id,
            vehicle_name=vehicle.vehicle_name,
            driver_name=vehicle.driver_name,
            operational_status="TRIP COMPLETED",
            trip_status="completed",
            speed_kmh=0.0,
            rpm=0.0,
            throttle_position_percent=None,
            brake_percent=None,
            fuel_level_percent=vehicle.fuel_level_percent,
            coolant_temperature_c=vehicle.coolant_temperature_c,
            engine_load_percent=None,
            overall_health_score=vehicle.overall_health_score,
            overall_health_status=vehicle.overall_health_status,
            engine_health=vehicle.engine_health,
            cooling_health=vehicle.cooling_health,
            brake_health=vehicle.brake_health,
            transmission_health=vehicle.transmission_health,
            fuel_system_health=vehicle.fuel_system_health,
            engine_health_status=vehicle.engine_health_status,
            cooling_health_status=vehicle.cooling_health_status,
            brake_health_status=vehicle.brake_health_status,
            transmission_health_status=vehicle.transmission_health_status,
            fuel_system_health_status=vehicle.fuel_system_health_status,
            health_reasons=vehicle.health_reasons,
            driver_safety_score=vehicle.driver_safety_score,
            driver_risk_level=vehicle.driver_risk_level,
            active_alert_count=0,
            active_alert_text=None,
            active_event_types=(),
            speeding=False,
            aggressive_throttle=False,
            harsh_braking=False,
            high_rpm=False,
            odometer_km=vehicle.odometer_km,
            last_updated_at=completed_at,
            route_id=vehicle.route_id,
            route_name=vehicle.route_name,
            trip_started_at=vehicle.trip_started_at,
            trip_distance_km=vehicle.trip_distance_km,
            fuel_rate_lph=0.0,
            fuel_used_liters=vehicle.fuel_used_liters,
        )

        self._latest[vehicle_id] = completed

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
            else None
        )

        attention_required = sum(
            1
            for v in vehicles
            if v.active_alert_count > 0
        )

        return DashboardSnapshot(
            timestamp=completed_at,
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
