from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from backend.analytics.driver_statistics.safety import compute_grade

_SEVERITY_RANK = {
    "normal": 0,
    "minor": 1,
    "moderate": 2,
    "severe": 3,
}

_EVENT_TYPE_LABELS = {
    "speeding": "Speeding",
    "harsh_braking": "Harsh Braking",
    "aggressive_throttle": "Aggressive Throttle",
    "high_rpm": "High RPM",
}


class TripDeleteResult(BaseModel):
    deleted_count: int


class TripRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    trip_id: str
    status: str

    vehicle_id: str
    vehicle_name: str | None = None
    driver_id: str
    driver_name: str | None = None
    route_id: str
    route_name: str | None = None
    route_type: str | None = None

    started_at: datetime
    completed_at: datetime | None

    distance_km: float | None
    duration_seconds: int | None
    fuel_consumed_liters: float | None
    average_speed_kmh: float | None
    maximum_speed_kmh: float | None
    average_fuel_rate_lph: float | None = None
    safety_score: float | None
    grade: str | None = None

    speeding_event_count: int = 0
    speeding_duration_seconds: float = 0.0
    harsh_braking_count: int = 0
    aggressive_throttle_event_count: int = 0
    aggressive_throttle_duration_seconds: float = 0.0
    high_rpm_event_count: int = 0
    high_rpm_duration_seconds: float = 0.0
    severe_event_count: int = 0
    moderate_event_count: int = 0
    minor_event_count: int = 0
    overall_severity: str | None = None
    events: list[dict] = []

    @classmethod
    def from_trip(cls, trip: "Trip") -> "TripRead":
        """Build a read model from a persisted trip, computing the
        derived fields (grade, average fuel rate, route name, behaviour
        counts) that are not columns on the ``trips`` table.
        """
        events = list(getattr(trip, "behaviour_events", None) or ())

        severity = "normal"
        for event in events:
            rank = _SEVERITY_RANK.get(event.severity, 0)
            if rank > _SEVERITY_RANK.get(severity, 0):
                severity = event.severity

        event_dicts = [
            {
                "event_type": event.event_type,
                "label": _EVENT_TYPE_LABELS.get(
                    event.event_type,
                    event.event_type,
                ),
                "started_at": event.started_at.isoformat(),
                "ended_at": event.ended_at.isoformat(),
                "duration_seconds": event.duration_seconds,
                "distance_km": event.distance_km,
                "severity": event.severity,
            }
            for event in events
        ]

        average_fuel_rate_lph = None
        if trip.fuel_used_liters is not None and trip.duration_seconds:
            hours = trip.duration_seconds / 3600.0
            if hours > 0:
                average_fuel_rate_lph = round(
                    trip.fuel_used_liters / hours,
                    2,
                )

        grade = (
            compute_grade(trip.trip_score)
            if trip.trip_score is not None
            else None
        )

        route = getattr(trip, "route", None)
        vehicle = getattr(trip, "vehicle", None)
        driver = getattr(trip, "driver", None)

        vehicle_name = None
        if vehicle is not None:
            vehicle_name = f"{vehicle.year} {vehicle.manufacturer} {vehicle.model}"

        driver_name = None
        if driver is not None:
            driver_name = f"{driver.first_name} {driver.last_name}".strip()

        return cls(
            trip_id=trip.trip_id,
            status=trip.status,
            vehicle_id=trip.vehicle_id,
            vehicle_name=vehicle_name,
            driver_id=trip.driver_id,
            driver_name=driver_name,
            route_id=trip.route_id,
            route_name=route.name if route is not None else None,
            route_type=route.route_type if route is not None else None,
            started_at=trip.start_time,
            completed_at=trip.end_time,
            distance_km=trip.distance_km,
            duration_seconds=trip.duration_seconds,
            fuel_consumed_liters=trip.fuel_used_liters,
            average_speed_kmh=trip.average_speed_kmh,
            maximum_speed_kmh=trip.maximum_speed_kmh,
            average_fuel_rate_lph=average_fuel_rate_lph,
            safety_score=trip.trip_score,
            grade=grade,
            speeding_event_count=sum(
                1 for e in events if e.event_type == "speeding"
            ),
            speeding_duration_seconds=round(
                sum(e.duration_seconds for e in events if e.event_type == "speeding"),
                2,
            ),
            harsh_braking_count=sum(
                1 for e in events if e.event_type == "harsh_braking"
            ),
            aggressive_throttle_event_count=sum(
                1 for e in events if e.event_type == "aggressive_throttle"
            ),
            aggressive_throttle_duration_seconds=round(
                sum(
                    e.duration_seconds
                    for e in events
                    if e.event_type == "aggressive_throttle"
                ),
                2,
            ),
            high_rpm_event_count=sum(
                1 for e in events if e.event_type == "high_rpm"
            ),
            high_rpm_duration_seconds=round(
                sum(e.duration_seconds for e in events if e.event_type == "high_rpm"),
                2,
            ),
            severe_event_count=sum(
                1 for e in events if e.severity == "severe"
            ),
            moderate_event_count=sum(
                1 for e in events if e.severity == "moderate"
            ),
            minor_event_count=sum(
                1 for e in events if e.severity == "minor"
            ),
            overall_severity=severity,
            events=event_dicts,
        )
