from __future__ import annotations

from pydantic import BaseModel


class KpiValue(BaseModel):
    label: str
    value: float | int | None
    unit: str | None = None
    previous_value: float | int | None = None
    change_pct: float | None = None
    change_direction: str | None = None  # "up" | "down" | "flat" | None
    data_quality: str = "valid"  # "valid" | "insufficient" | "no_data"
    context: str | None = None


class SummaryResponse(BaseModel):
    period_start: str
    period_end: str
    previous_start: str
    previous_end: str
    kpis: list[KpiValue]


class DailyTrendPoint(BaseModel):
    date: str
    value: float | None = None
    count: int | None = None


class FleetTrendResponse(BaseModel):
    safety_score_trend: list[DailyTrendPoint]
    event_rate_trend: list[DailyTrendPoint]
    fuel_efficiency_trend: list[DailyTrendPoint]
    trip_count_trend: list[DailyTrendPoint]


class DriverRankingRow(BaseModel):
    driver_id: str
    driver_name: str
    safety_score: float | None = None
    completed_trips: int = 0
    event_rate: float | None = None
    fuel_efficiency: float | None = None
    total_distance_km: float | None = None
    data_quality: str = "valid"


class DriverRankingResponse(BaseModel):
    drivers: list[DriverRankingRow]


class DriverTrendPoint(BaseModel):
    date: str
    trip_id: str | None = None
    score: float | None = None
    distance_km: float | None = None


class DriverTrendResponse(BaseModel):
    driver_id: str
    driver_name: str
    observations: list[DriverTrendPoint]
    data_quality: str = "valid"
    context: str | None = None


class SafetyDistributionBucket(BaseModel):
    range_label: str
    count: int = 0


class SafetyDistributionResponse(BaseModel):
    buckets: list[SafetyDistributionBucket]
    total_drivers: int = 0
    data_quality: str = "valid"


class VehicleRow(BaseModel):
    vehicle_id: str
    vehicle_name: str
    registration_number: str | None = None
    health_score: float | None = None
    health_status: str | None = None
    completed_trips: int = 0
    total_distance_km: float | None = None
    fuel_efficiency: float | None = None
    event_count: int = 0
    event_rate: float | None = None


class VehicleAnalyticsResponse(BaseModel):
    vehicles: list[VehicleRow]


class TripSummaryResponse(BaseModel):
    completed_trips: int = 0
    aborted_trips: int = 0
    total_distance_km: float | None = None
    avg_distance_km: float | None = None
    avg_duration_seconds: float | None = None
    total_driving_time_seconds: int | None = None
    avg_fuel_efficiency: float | None = None
    events_per_trip: float | None = None
    events_per_100km: float | None = None
    data_quality: str = "valid"


class EventBreakdownItem(BaseModel):
    event_type: str
    count: int = 0
    rate_per_100km: float | None = None


class EventBreakdownResponse(BaseModel):
    breakdown: list[EventBreakdownItem]
    total_events: int = 0
    total_distance_km: float | None = None


class EventTrendPoint(BaseModel):
    date: str
    speeding: int = 0
    harsh_braking: int = 0
    aggressive_throttle: int = 0
    high_rpm: int = 0
    total: int = 0


class EventTrendResponse(BaseModel):
    trend: list[EventTrendPoint]


class InsightItem(BaseModel):
    id: str
    category: str
    title: str
    description: str
    metric_value: str | None = None
    change_pct: float | None = None
    change_direction: str | None = None
    data_quality: str = "valid"


class InsightsResponse(BaseModel):
    insights: list[InsightItem]
