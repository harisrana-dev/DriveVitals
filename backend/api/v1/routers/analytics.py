from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import case, cast, func, Date, String, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.v1.dependencies import get_session
from backend.api.v1.schemas.analytics import (
    DailyTrendPoint,
    DriverRankingResponse,
    DriverRankingRow,
    DriverTrendPoint,
    DriverTrendResponse,
    EventBreakdownItem,
    EventBreakdownResponse,
    EventTrendPoint,
    EventTrendResponse,
    FleetTrendResponse,
    InsightItem,
    InsightsResponse,
    KpiValue,
    SafetyDistributionBucket,
    SafetyDistributionResponse,
    SummaryResponse,
    TripSummaryResponse,
    VehicleAnalyticsResponse,
    VehicleRow,
)
from backend.db.models.behaviour_event import BehaviourEvent
from backend.db.models.driver import Driver
from backend.db.models.driver_statistics import DriverStatistics
from backend.db.models.trip import Trip
from backend.db.models.vehicle import Vehicle
from backend.db.models.vehicle_health import VehicleHealth

router = APIRouter(prefix="/analytics")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_DEFAULT_RANGE = "last_30_days"


def _parse_range(
    range_key: str | None,
    custom_start: str | None,
    custom_end: str | None,
) -> tuple[datetime, datetime]:
    now = datetime.now(timezone.utc)
    key = range_key or _DEFAULT_RANGE
    if key == "last_7_days":
        start = now - timedelta(days=7)
    elif key == "last_30_days":
        start = now - timedelta(days=30)
    elif key == "last_90_days":
        start = now - timedelta(days=90)
    elif key == "last_6_months":
        start = now - timedelta(days=182)
    elif key == "custom" and custom_start and custom_end:
        start = datetime.fromisoformat(custom_start).replace(tzinfo=timezone.utc)
        now = datetime.fromisoformat(custom_end).replace(tzinfo=timezone.utc)
    else:
        start = now - timedelta(days=30)
    return start, now


def _previous_period(
    start: datetime, end: datetime
) -> tuple[datetime, datetime]:
    duration = end - start
    return start - duration, start


def _date_label(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d")


def _insufficient_context(obs_count: int, required: int = 3) -> str | None:
    if obs_count < required:
        return f"Insufficient data ({obs_count} observations, minimum {required})"
    return None


# ---------------------------------------------------------------------------
# GET /analytics/summary
# ---------------------------------------------------------------------------


@router.get(
    "/summary",
    response_model=SummaryResponse,
    summary="Fleet KPI summary",
    tags=["Analytics"],
)
async def get_summary(
    range_key: str | None = Query(default=None, alias="range"),
    custom_start: str | None = Query(default=None),
    custom_end: str | None = Query(default=None),
    vehicle_id: str | None = Query(default=None),
    driver_id: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
) -> SummaryResponse:
    start, end = _parse_range(range_key, custom_start, custom_end)
    prev_start, prev_end = _previous_period(start, end)

    # --- Completed trips in current period ---
    trip_filters = [
        Trip.status == "completed",
        Trip.start_time >= start,
        Trip.start_time < end,
    ]
    if vehicle_id:
        trip_filters.append(Trip.vehicle_id == vehicle_id)
    if driver_id:
        trip_filters.append(Trip.driver_id == driver_id)

    curr_trips = await session.execute(
        select(
            func.count(Trip.trip_id),
            func.coalesce(func.sum(Trip.distance_km), 0),
            func.coalesce(func.sum(Trip.fuel_used_liters), 0),
            func.avg(Trip.trip_score),
        ).where(*trip_filters)
    )
    row = curr_trips.one()
    c_completed = row[0]
    c_distance = float(row[1])
    c_fuel = float(row[2])
    c_avg_score = float(row[3]) if row[3] is not None else None

    # --- Previous period trips ---
    prev_trip_filters = [
        Trip.status == "completed",
        Trip.start_time >= prev_start,
        Trip.start_time < prev_end,
    ]
    if vehicle_id:
        prev_trip_filters.append(Trip.vehicle_id == vehicle_id)
    if driver_id:
        prev_trip_filters.append(Trip.driver_id == driver_id)

    prev_trips = await session.execute(
        select(
            func.count(Trip.trip_id),
            func.coalesce(func.sum(Trip.distance_km), 0),
            func.coalesce(func.sum(Trip.fuel_used_liters), 0),
            func.avg(Trip.trip_score),
        ).where(*prev_trip_filters)
    )
    prow = prev_trips.one()
    p_completed = prow[0]
    p_distance = float(prow[1])
    p_fuel = float(prow[2])
    p_avg_score = float(prow[3]) if prow[3] is not None else None

    # --- Events in current period ---
    event_filters = [
        BehaviourEvent.started_at >= start,
        BehaviourEvent.started_at < end,
    ]
    if vehicle_id:
        event_filters.append(BehaviourEvent.vehicle_id == vehicle_id)
    if driver_id:
        event_filters.append(BehaviourEvent.driver_id == driver_id)

    curr_events = await session.execute(
        select(func.count(BehaviourEvent.event_id)).where(*event_filters)
    )
    c_events = curr_events.scalar() or 0

    prev_event_filters = [
        BehaviourEvent.started_at >= prev_start,
        BehaviourEvent.started_at < prev_end,
    ]
    if vehicle_id:
        prev_event_filters.append(BehaviourEvent.vehicle_id == vehicle_id)
    if driver_id:
        prev_event_filters.append(BehaviourEvent.driver_id == driver_id)

    prev_events = await session.execute(
        select(func.count(BehaviourEvent.event_id)).where(*prev_event_filters)
    )
    p_events = prev_events.scalar() or 0

    # --- Fleet fuel efficiency ---
    c_fuel_eff = (c_distance / c_fuel) if c_fuel > 0 else None
    p_fuel_eff = (p_distance / p_fuel) if p_fuel > 0 else None

    # --- Vehicle health average ---
    health_q = await session.execute(
        select(func.avg(VehicleHealth.overall_health_score))
    )
    health_val = health_q.scalar()
    c_health = float(health_val) if health_val is not None else None

    def _change(curr: float | None, prev: float | None) -> tuple[float | None, str | None]:
        if curr is None or prev is None or prev == 0:
            return None, None
        pct = ((curr - prev) / abs(prev)) * 100
        direction = "up" if pct > 0 else ("down" if pct < 0 else "flat")
        return round(pct, 1), direction

    kpis = [
        KpiValue(
            label="Safety Score",
            value=round(c_avg_score, 1) if c_avg_score is not None else None,
            unit="/ 100",
            previous_value=round(p_avg_score, 1) if p_avg_score is not None else None,
            change_pct=_change(c_avg_score, p_avg_score)[0],
            change_direction=_change(c_avg_score, p_avg_score)[1],
            data_quality="valid" if c_avg_score is not None else "no_data",
            context=f"{c_completed} completed trips",
        ),
        KpiValue(
            label="Completed Trips",
            value=c_completed,
            previous_value=p_completed,
            change_pct=_change(float(c_completed), float(p_completed))[0],
            change_direction=_change(float(c_completed), float(p_completed))[1],
            data_quality="valid" if c_completed > 0 else "no_data",
        ),
        KpiValue(
            label="Fleet Fuel Efficiency",
            value=round(c_fuel_eff, 1) if c_fuel_eff is not None else None,
            unit="km/L",
            previous_value=round(p_fuel_eff, 1) if p_fuel_eff is not None else None,
            change_pct=_change(c_fuel_eff, p_fuel_eff)[0],
            change_direction=_change(c_fuel_eff, p_fuel_eff)[1],
            data_quality="valid" if c_fuel_eff is not None else "no_data",
            context=f"from {c_completed} trips",
        ),
        KpiValue(
            label="Safety Events",
            value=c_events,
            previous_value=p_events,
            change_pct=_change(float(c_events), float(p_events))[0],
            change_direction=_change(float(c_events), float(p_events))[1],
            data_quality="valid" if c_events > 0 else "no_data",
            context=f"in {c_completed} completed trips",
        ),
        KpiValue(
            label="Vehicle Health",
            value=round(c_health, 1) if c_health is not None else None,
            unit="avg score",
            previous_value=None,
            change_pct=None,
            change_direction=None,
            data_quality="valid" if c_health is not None else "no_data",
        ),
    ]

    return SummaryResponse(
        period_start=_date_label(start),
        period_end=_date_label(end),
        previous_start=_date_label(prev_start),
        previous_end=_date_label(prev_end),
        kpis=kpis,
    )


# ---------------------------------------------------------------------------
# GET /analytics/fleet-trend
# ---------------------------------------------------------------------------


@router.get(
    "/fleet-trend",
    response_model=FleetTrendResponse,
    summary="Fleet historical trends",
    tags=["Analytics"],
)
async def get_fleet_trend(
    range_key: str | None = Query(default=None, alias="range"),
    custom_start: str | None = Query(default=None),
    custom_end: str | None = Query(default=None),
    vehicle_id: str | None = Query(default=None),
    driver_id: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
) -> FleetTrendResponse:
    start, end = _parse_range(range_key, custom_start, custom_end)

    # --- Safety score trend (per day, from completed trips) ---
    trip_filters = [
        Trip.status == "completed",
        Trip.start_time >= start,
        Trip.start_time < end,
    ]
    if vehicle_id:
        trip_filters.append(Trip.vehicle_id == vehicle_id)
    if driver_id:
        trip_filters.append(Trip.driver_id == driver_id)

    safety_rows = await session.execute(
        select(
            cast(Trip.start_time, Date).label("day"),
            func.avg(Trip.trip_score),
            func.count(Trip.trip_id),
        )
        .where(*trip_filters)
        .group_by(cast(Trip.start_time, Date))
        .order_by(cast(Trip.start_time, Date))
    )
    safety_trend = [
        DailyTrendPoint(
            date=r[0].isoformat() if r[0] else "",
            value=round(float(r[1]), 2) if r[1] is not None else None,
            count=r[2],
        )
        for r in safety_rows
    ]

    # --- Event rate trend (per day, events / 100 km) ---
    event_filters = [
        BehaviourEvent.started_at >= start,
        BehaviourEvent.started_at < end,
    ]
    if vehicle_id:
        event_filters.append(BehaviourEvent.vehicle_id == vehicle_id)
    if driver_id:
        event_filters.append(BehaviourEvent.driver_id == driver_id)

    event_rows = await session.execute(
        select(
            cast(BehaviourEvent.started_at, Date).label("day"),
            func.count(BehaviourEvent.event_id),
        )
        .where(*event_filters)
        .group_by(cast(BehaviourEvent.started_at, Date))
        .order_by(cast(BehaviourEvent.started_at, Date))
    )

    # Get daily distance for normalisation
    daily_distance_rows = await session.execute(
        select(
            cast(Trip.start_time, Date).label("day"),
            func.coalesce(func.sum(Trip.distance_km), 0),
        )
        .where(*trip_filters)
        .group_by(cast(Trip.start_time, Date))
    )
    dist_by_day = {r[0]: float(r[1]) for r in daily_distance_rows}

    event_trend = []
    for r in event_rows:
        day = r[0]
        events = r[1]
        dist = dist_by_day.get(day, 0)
        rate = round((events / dist) * 100, 2) if dist > 0 else None
        event_trend.append(
            DailyTrendPoint(date=day.isoformat() if day else "", value=rate, count=events)
        )

    # --- Fuel efficiency trend ---
    fuel_rows = await session.execute(
        select(
            cast(Trip.start_time, Date).label("day"),
            func.sum(Trip.distance_km),
            func.sum(Trip.fuel_used_liters),
        )
        .where(*trip_filters)
        .where(Trip.fuel_used_liters > 0)
        .group_by(cast(Trip.start_time, Date))
        .order_by(cast(Trip.start_time, Date))
    )
    fuel_trend = []
    for r in fuel_rows:
        dist = float(r[1]) if r[1] else 0
        fuel = float(r[2]) if r[2] else 0
        eff = round(dist / fuel, 1) if fuel > 0 else None
        fuel_trend.append(DailyTrendPoint(date=r[0].isoformat() if r[0] else "", value=eff))

    # --- Trip count trend ---
    trip_count_rows = await session.execute(
        select(
            cast(Trip.start_time, Date).label("day"),
            func.count(Trip.trip_id),
        )
        .where(*trip_filters)
        .group_by(cast(Trip.start_time, Date))
        .order_by(cast(Trip.start_time, Date))
    )
    trip_trend = [
        DailyTrendPoint(date=r[0].isoformat() if r[0] else "", count=r[1])
        for r in trip_count_rows
    ]

    return FleetTrendResponse(
        safety_score_trend=safety_trend,
        event_rate_trend=event_trend,
        fuel_efficiency_trend=fuel_trend,
        trip_count_trend=trip_trend,
    )


# ---------------------------------------------------------------------------
# GET /analytics/drivers
# ---------------------------------------------------------------------------


@router.get(
    "/drivers",
    response_model=DriverRankingResponse,
    summary="Driver performance ranking",
    tags=["Analytics"],
)
async def get_driver_ranking(
    range_key: str | None = Query(default=None, alias="range"),
    custom_start: str | None = Query(default=None),
    custom_end: str | None = Query(default=None),
    vehicle_id: str | None = Query(default=None),
    driver_id: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
) -> DriverRankingResponse:
    start, end = _parse_range(range_key, custom_start, custom_end)

    trip_filters = [
        Trip.status == "completed",
        Trip.start_time >= start,
        Trip.start_time < end,
    ]
    if vehicle_id:
        trip_filters.append(Trip.vehicle_id == vehicle_id)
    if driver_id:
        trip_filters.append(Trip.driver_id == driver_id)

    # Get driver stats within date range
    driver_stats_rows = await session.execute(
        select(
            Trip.driver_id,
            Driver.first_name,
            Driver.last_name,
            func.count(Trip.trip_id).label("completed_trips"),
            func.coalesce(func.sum(Trip.distance_km), 0).label("total_distance"),
            func.coalesce(func.sum(Trip.fuel_used_liters), 0).label("total_fuel"),
            func.avg(Trip.trip_score).label("avg_score"),
        )
        .join(Driver, Trip.driver_id == Driver.driver_id)
        .where(*trip_filters)
        .group_by(Trip.driver_id, Driver.first_name, Driver.last_name)
    )
    driver_rows = driver_stats_rows.all()

    # Get event counts per driver in date range
    event_filters = [
        BehaviourEvent.started_at >= start,
        BehaviourEvent.started_at < end,
    ]
    if vehicle_id:
        event_filters.append(BehaviourEvent.vehicle_id == vehicle_id)
    if driver_id:
        event_filters.append(BehaviourEvent.driver_id == driver_id)

    event_counts = await session.execute(
        select(
            BehaviourEvent.driver_id,
            func.count(BehaviourEvent.event_id),
        )
        .where(*event_filters)
        .group_by(BehaviourEvent.driver_id)
    )
    events_by_driver = {r[0]: r[1] for r in event_counts}

    drivers = []
    for r in driver_rows:
        did = r[0]
        total_distance = float(r[4])
        total_fuel = float(r[5])
        avg_score = float(r[6]) if r[6] is not None else None
        event_count = events_by_driver.get(did, 0)
        fuel_eff = round(total_distance / total_fuel, 1) if total_fuel > 0 else None
        event_rate = round((event_count / total_distance) * 100, 2) if total_distance > 0 else None

        drivers.append(
            DriverRankingRow(
                driver_id=did,
                driver_name=f"{r[1]} {r[2]}".strip(),
                safety_score=round(avg_score, 1) if avg_score is not None else None,
                completed_trips=r[3],
                event_rate=event_rate,
                fuel_efficiency=fuel_eff,
                total_distance_km=round(total_distance, 1),
                data_quality="valid" if avg_score is not None else "no_data",
            )
        )

    drivers.sort(
        key=lambda d: (d.safety_score if d.safety_score is not None else -1),
        reverse=True,
    )

    return DriverRankingResponse(drivers=drivers)


# ---------------------------------------------------------------------------
# GET /analytics/drivers/{driver_id}/trend
# ---------------------------------------------------------------------------


@router.get(
    "/drivers/{driver_id}/trend",
    response_model=DriverTrendResponse,
    summary="Individual driver performance trend",
    tags=["Analytics"],
)
async def get_driver_trend(
    driver_id: str,
    range_key: str | None = Query(default=None, alias="range"),
    custom_start: str | None = Query(default=None),
    custom_end: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
) -> DriverTrendResponse:
    start, end = _parse_range(range_key, custom_start, custom_end)

    # Get driver name
    driver_row = await session.execute(
        select(Driver.first_name, Driver.last_name).where(Driver.driver_id == driver_id)
    )
    d = driver_row.first()
    driver_name = f"{d[0]} {d[1]}".strip() if d else driver_id

    # Get completed trip scores over time
    trip_rows = await session.execute(
        select(
            Trip.start_time,
            Trip.trip_id,
            Trip.trip_score,
            Trip.distance_km,
        )
        .where(
            Trip.driver_id == driver_id,
            Trip.status == "completed",
            Trip.start_time >= start,
            Trip.start_time < end,
        )
        .order_by(Trip.start_time)
    )

    observations = []
    for r in trip_rows:
        observations.append(
            DriverTrendPoint(
                date=r[0].isoformat() if r[0] else "",
                trip_id=r[1],
                score=round(float(r[2]), 2) if r[2] is not None else None,
                distance_km=round(float(r[3]), 2) if r[3] is not None else None,
            )
        )

    quality = "valid"
    context = None
    if len(observations) < 3:
        quality = "insufficient"
        context = f"Only {len(observations)} completed trips in this period"

    return DriverTrendResponse(
        driver_id=driver_id,
        driver_name=driver_name,
        observations=observations,
        data_quality=quality,
        context=context,
    )


# ---------------------------------------------------------------------------
# GET /analytics/safety-distribution
# ---------------------------------------------------------------------------


@router.get(
    "/safety-distribution",
    response_model=SafetyDistributionResponse,
    summary="Driver safety score distribution",
    tags=["Analytics"],
)
async def get_safety_distribution(
    session: AsyncSession = Depends(get_session),
) -> SafetyDistributionResponse:
    rows = await session.execute(select(DriverStatistics.safety_score))
    scores = [float(r[0]) for r in rows if r[0] is not None]

    if len(scores) < 2:
        return SafetyDistributionResponse(
            buckets=[],
            total_drivers=len(scores),
            data_quality="insufficient",
        )

    buckets_def = [
        ("90–100", 90, 101),
        ("80–89", 80, 90),
        ("70–79", 70, 80),
        ("60–69", 60, 70),
        ("< 60", 0, 60),
    ]
    buckets = []
    for label, lo, hi in buckets_def:
        count = sum(1 for s in scores if lo <= s < hi)
        buckets.append(SafetyDistributionBucket(range_label=label, count=count))

    return SafetyDistributionResponse(
        buckets=buckets,
        total_drivers=len(scores),
        data_quality="valid",
    )


# ---------------------------------------------------------------------------
# GET /analytics/vehicles
# ---------------------------------------------------------------------------


@router.get(
    "/vehicles",
    response_model=VehicleAnalyticsResponse,
    summary="Vehicle analytics",
    tags=["Analytics"],
)
async def get_vehicle_analytics(
    range_key: str | None = Query(default=None, alias="range"),
    custom_start: str | None = Query(default=None),
    custom_end: str | None = Query(default=None),
    vehicle_id: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
) -> VehicleAnalyticsResponse:
    start, end = _parse_range(range_key, custom_start, custom_end)

    trip_filters = [
        Trip.status == "completed",
        Trip.start_time >= start,
        Trip.start_time < end,
    ]
    if vehicle_id:
        trip_filters.append(Trip.vehicle_id == vehicle_id)

    # Trip stats per vehicle
    trip_rows = await session.execute(
        select(
            Trip.vehicle_id,
            func.count(Trip.trip_id).label("completed_trips"),
            func.coalesce(func.sum(Trip.distance_km), 0).label("total_distance"),
            func.coalesce(func.sum(Trip.fuel_used_liters), 0).label("total_fuel"),
        )
        .where(*trip_filters)
        .group_by(Trip.vehicle_id)
    )
    trip_data = {r[0]: (r[1], float(r[2]), float(r[3])) for r in trip_rows}

    # Event counts per vehicle
    event_filters = [
        BehaviourEvent.started_at >= start,
        BehaviourEvent.started_at < end,
    ]
    if vehicle_id:
        event_filters.append(BehaviourEvent.vehicle_id == vehicle_id)

    event_counts = await session.execute(
        select(
            BehaviourEvent.vehicle_id,
            func.count(BehaviourEvent.event_id),
        )
        .where(*event_filters)
        .group_by(BehaviourEvent.vehicle_id)
    )
    events_by_vehicle = {r[0]: r[1] for r in event_counts}

    # Vehicle info + health
    vehicle_q = await session.execute(select(Vehicle))
    vehicles = vehicle_q.scalars().all()

    health_q = await session.execute(select(VehicleHealth))
    health_map = {h.vehicle_id: h for h in health_q.scalars().all()}

    result = []
    for v in vehicles:
        vid = v.vehicle_id
        trips_info = trip_data.get(vid, (0, 0, 0))
        completed, dist, fuel = trips_info
        event_count = events_by_vehicle.get(vid, 0)
        health = health_map.get(vid)
        fuel_eff = round(dist / fuel, 1) if fuel > 0 else None
        event_rate = round((event_count / dist) * 100, 2) if dist > 0 else None
        h_status = None
        if health and health.overall_health_score is not None:
            if health.overall_health_score >= 90:
                h_status = "healthy"
            elif health.overall_health_score >= 70:
                h_status = "warning"
            else:
                h_status = "critical"

        result.append(
            VehicleRow(
                vehicle_id=vid,
                vehicle_name=f"{v.manufacturer} {v.model}".strip(),
                registration_number=v.registration_number,
                health_score=round(health.overall_health_score, 1) if health and health.overall_health_score is not None else None,
                health_status=h_status,
                completed_trips=completed,
                total_distance_km=round(dist, 1),
                fuel_efficiency=fuel_eff,
                event_count=event_count,
                event_rate=event_rate,
            )
        )

    result.sort(key=lambda v: v.completed_trips, reverse=True)

    return VehicleAnalyticsResponse(vehicles=result)


# ---------------------------------------------------------------------------
# GET /analytics/trips
# ---------------------------------------------------------------------------


@router.get(
    "/trips",
    response_model=TripSummaryResponse,
    summary="Trip analytics summary",
    tags=["Analytics"],
)
async def get_trip_analytics(
    range_key: str | None = Query(default=None, alias="range"),
    custom_start: str | None = Query(default=None),
    custom_end: str | None = Query(default=None),
    vehicle_id: str | None = Query(default=None),
    driver_id: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
) -> TripSummaryResponse:
    start, end = _parse_range(range_key, custom_start, custom_end)

    # Completed trips
    comp_filters = [
        Trip.status == "completed",
        Trip.start_time >= start,
        Trip.start_time < end,
    ]
    if vehicle_id:
        comp_filters.append(Trip.vehicle_id == vehicle_id)
    if driver_id:
        comp_filters.append(Trip.driver_id == driver_id)

    comp = await session.execute(
        select(
            func.count(Trip.trip_id),
            func.coalesce(func.sum(Trip.distance_km), 0),
            func.avg(Trip.distance_km),
            func.avg(Trip.duration_seconds),
            func.coalesce(func.sum(Trip.duration_seconds), 0),
            func.coalesce(func.sum(Trip.fuel_used_liters), 0),
        ).where(*comp_filters)
    )
    cr = comp.one()
    c_count = cr[0]
    c_distance = float(cr[1])
    c_avg_dist = float(cr[2]) if cr[2] is not None else None
    c_avg_dur = float(cr[3]) if cr[3] is not None else None
    c_total_dur = int(cr[4])
    c_fuel = float(cr[5])

    # Aborted trips
    abort_filters = [
        Trip.status == "aborted",
        Trip.start_time >= start,
        Trip.start_time < end,
    ]
    if vehicle_id:
        abort_filters.append(Trip.vehicle_id == vehicle_id)
    if driver_id:
        abort_filters.append(Trip.driver_id == driver_id)

    abort_count = await session.execute(
        select(func.count(Trip.trip_id)).where(*abort_filters)
    )
    a_count = abort_count.scalar() or 0

    # Events in completed trips only
    ev_filters = [
        Trip.status == "completed",
        Trip.start_time >= start,
        Trip.start_time < end,
    ]
    if vehicle_id:
        ev_filters.append(Trip.vehicle_id == vehicle_id)
    if driver_id:
        ev_filters.append(Trip.driver_id == driver_id)

    ev = await session.execute(
        select(func.count(BehaviourEvent.event_id))
        .join(Trip, BehaviourEvent.trip_id == Trip.trip_id)
        .where(*ev_filters)
    )
    total_events = ev.scalar() or 0

    fuel_eff = round(c_distance / c_fuel, 1) if c_fuel > 0 else None
    events_per_trip = round(total_events / c_count, 1) if c_count > 0 else None
    events_per_100km = round((total_events / c_distance) * 100, 1) if c_distance > 0 else None

    return TripSummaryResponse(
        completed_trips=c_count,
        aborted_trips=a_count,
        total_distance_km=round(c_distance, 1) if c_distance > 0 else None,
        avg_distance_km=round(c_avg_dist, 1) if c_avg_dist is not None else None,
        avg_duration_seconds=round(c_avg_dur) if c_avg_dur is not None else None,
        total_driving_time_seconds=c_total_dur if c_total_dur > 0 else None,
        avg_fuel_efficiency=fuel_eff,
        events_per_trip=events_per_trip,
        events_per_100km=events_per_100km,
        data_quality="valid" if c_count > 0 else "no_data",
    )


# ---------------------------------------------------------------------------
# GET /analytics/events
# ---------------------------------------------------------------------------


@router.get(
    "/events",
    response_model=EventBreakdownResponse,
    summary="Event type breakdown",
    tags=["Analytics"],
)
async def get_event_breakdown(
    range_key: str | None = Query(default=None, alias="range"),
    custom_start: str | None = Query(default=None),
    custom_end: str | None = Query(default=None),
    vehicle_id: str | None = Query(default=None),
    driver_id: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
) -> EventBreakdownResponse:
    start, end = _parse_range(range_key, custom_start, custom_end)

    filters = [
        BehaviourEvent.started_at >= start,
        BehaviourEvent.started_at < end,
    ]
    if vehicle_id:
        filters.append(BehaviourEvent.vehicle_id == vehicle_id)
    if driver_id:
        filters.append(BehaviourEvent.driver_id == driver_id)

    rows = await session.execute(
        select(
            BehaviourEvent.event_type,
            func.count(BehaviourEvent.event_id),
        )
        .where(*filters)
        .group_by(BehaviourEvent.event_type)
    )

    # Get total distance for rate calculation
    trip_filters = [
        Trip.status == "completed",
        Trip.start_time >= start,
        Trip.start_time < end,
    ]
    if vehicle_id:
        trip_filters.append(Trip.vehicle_id == vehicle_id)
    if driver_id:
        trip_filters.append(Trip.driver_id == driver_id)

    dist_q = await session.execute(
        select(func.coalesce(func.sum(Trip.distance_km), 0)).where(*trip_filters)
    )
    total_distance = float(dist_q.scalar())

    total = 0
    breakdown = []
    for r in rows:
        count = r[1]
        total += count
        rate = round((count / total_distance) * 100, 2) if total_distance > 0 else None
        breakdown.append(
            EventBreakdownItem(event_type=r[0], count=count, rate_per_100km=rate)
        )

    breakdown.sort(key=lambda b: b.count, reverse=True)

    return EventBreakdownResponse(
        breakdown=breakdown,
        total_events=total,
        total_distance_km=round(total_distance, 1) if total_distance > 0 else None,
    )


# ---------------------------------------------------------------------------
# GET /analytics/events/trend
# ---------------------------------------------------------------------------


@router.get(
    "/events/trend",
    response_model=EventTrendResponse,
    summary="Event trend over time",
    tags=["Analytics"],
)
async def get_event_trend(
    range_key: str | None = Query(default=None, alias="range"),
    custom_start: str | None = Query(default=None),
    custom_end: str | None = Query(default=None),
    vehicle_id: str | None = Query(default=None),
    driver_id: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
) -> EventTrendResponse:
    start, end = _parse_range(range_key, custom_start, custom_end)

    filters = [
        BehaviourEvent.started_at >= start,
        BehaviourEvent.started_at < end,
    ]
    if vehicle_id:
        filters.append(BehaviourEvent.vehicle_id == vehicle_id)
    if driver_id:
        filters.append(BehaviourEvent.driver_id == driver_id)

    rows = await session.execute(
        select(
            cast(BehaviourEvent.started_at, Date).label("day"),
            BehaviourEvent.event_type,
            func.count(BehaviourEvent.event_id),
        )
        .where(*filters)
        .group_by(cast(BehaviourEvent.started_at, Date), BehaviourEvent.event_type)
        .order_by(cast(BehaviourEvent.started_at, Date))
    )

    # Aggregate by day
    day_data: dict[str, dict] = {}
    for r in rows:
        day = r[0].isoformat() if r[0] else ""
        etype = r[1]
        count = r[2]
        if day not in day_data:
            day_data[day] = {"speeding": 0, "harsh_braking": 0, "aggressive_throttle": 0, "high_rpm": 0}
        if etype in day_data[day]:
            day_data[day][etype] = count

    trend = []
    for day in sorted(day_data.keys()):
        d = day_data[day]
        total = sum(d.values())
        trend.append(
            EventTrendPoint(
                date=day,
                speeding=d["speeding"],
                harsh_braking=d["harsh_braking"],
                aggressive_throttle=d["aggressive_throttle"],
                high_rpm=d["high_rpm"],
                total=total,
            )
        )

    return EventTrendResponse(trend=trend)


# ---------------------------------------------------------------------------
# GET /analytics/insights
# ---------------------------------------------------------------------------


@router.get(
    "/insights",
    response_model=InsightsResponse,
    summary="Deterministic insights",
    tags=["Analytics"],
)
async def get_insights(
    range_key: str | None = Query(default=None, alias="range"),
    custom_start: str | None = Query(default=None),
    custom_end: str | None = Query(default=None),
    vehicle_id: str | None = Query(default=None),
    driver_id: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
) -> InsightsResponse:
    start, end = _parse_range(range_key, custom_start, custom_end)
    prev_start, prev_end = _previous_period(start, end)
    insights: list[InsightItem] = []

    def _make_id(category: str, title: str) -> str:
        return hashlib.md5(f"{category}:{title}".encode()).hexdigest()[:12]

    # --- Insight 1: Trip completion change ---
    trip_f = [Trip.status == "completed", Trip.start_time >= start, Trip.start_time < end]
    prev_f = [Trip.status == "completed", Trip.start_time >= prev_start, Trip.start_time < prev_end]
    if vehicle_id:
        trip_f.append(Trip.vehicle_id == vehicle_id)
        prev_f.append(Trip.vehicle_id == vehicle_id)
    if driver_id:
        trip_f.append(Trip.driver_id == driver_id)
        prev_f.append(Trip.driver_id == driver_id)

    curr_count = (await session.execute(select(func.count(Trip.trip_id)).where(*trip_f))).scalar() or 0
    prev_count = (await session.execute(select(func.count(Trip.trip_id)).where(*prev_f))).scalar() or 0
    if curr_count > 0 and prev_count > 0:
        change = ((curr_count - prev_count) / prev_count) * 100
        direction = "up" if change > 0 else "down"
        title = f"Completed trips {'increased' if direction == 'up' else 'decreased'} {abs(change):.0f}%"
        insights.append(
            InsightItem(
                id=_make_id("trips", title),
                category="trips",
                title=title,
                description=f"Fleet completed {curr_count} trips vs {prev_count} in the previous period.",
                metric_value=f"{curr_count}",
                change_pct=round(change, 1),
                change_direction=direction,
            )
        )

    # --- Insight 2: Event rate change ---
    ev_f = [BehaviourEvent.started_at >= start, BehaviourEvent.started_at < end]
    ev_prev = [BehaviourEvent.started_at >= prev_start, BehaviourEvent.started_at < prev_end]
    if vehicle_id:
        ev_f.append(BehaviourEvent.vehicle_id == vehicle_id)
        ev_prev.append(BehaviourEvent.vehicle_id == vehicle_id)
    if driver_id:
        ev_f.append(BehaviourEvent.driver_id == driver_id)
        ev_prev.append(BehaviourEvent.driver_id == driver_id)

    curr_events = (await session.execute(select(func.count(BehaviourEvent.event_id)).where(*ev_f))).scalar() or 0
    prev_events = (await session.execute(select(func.count(BehaviourEvent.event_id)).where(*ev_prev))).scalar() or 0
    if curr_events > 0 or prev_events > 0:
        if prev_events > 0:
            change = ((curr_events - prev_events) / prev_events) * 100
            direction = "up" if change > 0 else "down"
            ev_type = "increased" if direction == "up" else "decreased"
            title = f"Safety events {ev_type} {abs(change):.0f}%"
            insights.append(
                InsightItem(
                    id=_make_id("events", title),
                    category="safety",
                    title=title,
                    description=f"Fleet recorded {curr_events} events vs {prev_events} in the previous period.",
                    metric_value=str(curr_events),
                    change_pct=round(change, 1),
                    change_direction=direction,
                )
            )
        else:
            insights.append(
                InsightItem(
                    id=_make_id("events", f"{curr_events} events this period"),
                    category="safety",
                    title=f"{curr_events} safety events recorded",
                    description="No events in the previous period for comparison.",
                    metric_value=str(curr_events),
                )
            )

    # --- Insight 3: Highest event rate vehicle ---
    veh_ev = await session.execute(
        select(
            BehaviourEvent.vehicle_id,
            func.count(BehaviourEvent.event_id),
        )
        .where(*ev_f)
        .group_by(BehaviourEvent.vehicle_id)
    )
    veh_dist = await session.execute(
        select(
            Trip.vehicle_id,
            func.coalesce(func.sum(Trip.distance_km), 0),
        )
        .where(*trip_f)
        .group_by(Trip.vehicle_id)
    )
    dist_map = {r[0]: float(r[1]) for r in veh_dist}
    max_rate = 0
    max_vid = None
    for r in veh_ev:
        vid, cnt = r[0], r[1]
        dist = dist_map.get(vid, 0)
        rate = (cnt / dist) * 100 if dist > 0 else 0
        if rate > max_rate:
            max_rate = rate
            max_vid = vid
    if max_vid and max_rate > 0:
        v = (await session.execute(select(Vehicle).where(Vehicle.vehicle_id == max_vid))).scalar_one_or_none()
        vname = f"{v.manufacturer} {v.model}" if v else max_vid
        title = f"{vname} has the highest event rate at {max_rate:.1f} events / 100 km"
        insights.append(
            InsightItem(
                id=_make_id("vehicle_event_rate", title),
                category="safety",
                title=title,
                description=f"Vehicle {max_vid} recorded the highest event density in this period.",
                metric_value=f"{max_rate:.1f} / 100 km",
            )
        )

    # --- Insight 4: Fuel efficiency change ---
    fuel_f = trip_f + [Trip.fuel_used_liters > 0]
    fuel_prev = prev_f + [Trip.fuel_used_liters > 0]
    curr_fuel = await session.execute(
        select(
            func.coalesce(func.sum(Trip.distance_km), 0),
            func.coalesce(func.sum(Trip.fuel_used_liters), 0),
        ).where(*fuel_f)
    )
    cfr = curr_fuel.one()
    prev_fuel = await session.execute(
        select(
            func.coalesce(func.sum(Trip.distance_km), 0),
            func.coalesce(func.sum(Trip.fuel_used_liters), 0),
        ).where(*fuel_prev)
    )
    pfr = prev_fuel.one()
    c_eff = float(cfr[0]) / float(cfr[1]) if float(cfr[1]) > 0 else None
    p_eff = float(pfr[0]) / float(pfr[1]) if float(pfr[1]) > 0 else None
    if c_eff and p_eff:
        change = ((c_eff - p_eff) / p_eff) * 100
        direction = "up" if change > 0 else "down"
        title = f"Fuel efficiency {'improved' if direction == 'up' else 'declined'} {abs(change):.0f}%"
        insights.append(
            InsightItem(
                id=_make_id("fuel_eff", title),
                category="fuel",
                title=title,
                description=f"Fleet efficiency is {c_eff:.1f} km/L vs {p_eff:.1f} km/L in the previous period.",
                metric_value=f"{c_eff:.1f} km/L",
                change_pct=round(change, 1),
                change_direction=direction,
            )
        )

    # --- Insight 5: Top driver ---
    if not driver_id:
        top_driver = await session.execute(
            select(
                Trip.driver_id,
                Driver.first_name,
                Driver.last_name,
                func.count(Trip.trip_id),
                func.avg(Trip.trip_score),
            )
            .join(Driver, Trip.driver_id == Driver.driver_id)
            .where(*trip_f)
            .group_by(Trip.driver_id, Driver.first_name, Driver.last_name)
            .order_by(func.avg(Trip.trip_score).desc())
            .limit(1)
        )
        td = top_driver.first()
        if td and td[3] is not None:
            avg = float(td[4]) if td[4] is not None else 0
            title = f"{td[1]} {td[2]} completed {td[3]} trips with avg safety score {avg:.0f}"
            insights.append(
                InsightItem(
                    id=_make_id("top_driver", title),
                    category="drivers",
                    title=title,
                    description=f"Highest average safety score among drivers with completed trips in this period.",
                    metric_value=f"{avg:.0f} / 100",
                )
            )

    return InsightsResponse(insights=insights)
