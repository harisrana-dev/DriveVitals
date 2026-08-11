"""
Regression tests: maximum speed must be the observed telemetry peak.

The M4 mandate: a trip's ``maximum_speed_kmh`` must be the highest speed
actually observed during the trip. It must never be derived from
``speed_limit_kmh + maximum_speed_excess_kmh``, which produced plausible
but fabricated values (e.g. a reported peak even when the vehicle never
exceeded the limit).

These tests pin that contract at the fleet layer where the observed
peak is recorded.
"""

from datetime import datetime, timedelta, timezone

from backend.fleet.models.driver import BehaviorProfile, Driver
from backend.fleet.models.route import Route, RouteType
from backend.fleet.models.trip import Trip, TripStatus
from backend.fleet.models.vehicle import Vehicle
from backend.fleet.runtime.vehicle_runner import VehicleRunner


def _make_runner(
    distance_km: float = 1.0,
    speed_limit_kmh: float = 60.0,
) -> VehicleRunner:
    vehicle = Vehicle(
        vehicle_id="V-1",
        make="Ford",
        model="Transit",
        year=2023,
        odometer_km=1000.0,
        fuel_level_percent=90.0,
    )
    driver = Driver(
        driver_id="D-1",
        name="Test Driver",
        behavior_profile=BehaviorProfile.AGGRESSIVE,
    )
    route = Route(
        route_id="R-1",
        origin="Warehouse",
        destination="Customer A",
        distance_km=distance_km,
        route_type=RouteType.URBAN,
        speed_limit_kmh=speed_limit_kmh,
    )
    trip = Trip(
        trip_id="T-1",
        vehicle_id="V-1",
        driver_id="D-1",
        route_id="R-1",
    )
    return VehicleRunner(vehicle=vehicle, driver=driver, route=route, trip=trip)


def test_trip_record_speed_keeps_only_the_peak() -> None:
    trip = Trip(trip_id="T-1", vehicle_id="V-1", driver_id="D-1", route_id="R-1")

    assert trip.maximum_speed_kmh == 0.0

    trip.record_speed(40.0)
    assert trip.maximum_speed_kmh == 40.0

    trip.record_speed(30.0)
    assert trip.maximum_speed_kmh == 40.0

    trip.record_speed(52.5)
    assert trip.maximum_speed_kmh == 52.5


def test_runner_trip_tracks_observed_peak_speed() -> None:
    runner = _make_runner()
    start = datetime(2026, 8, 7, 10, 0, tzinfo=timezone.utc)

    observed_speeds: list[float] = []
    runner.start(now=start)
    now = start
    ticks = 0
    while not runner.is_complete():
        sample = runner.tick(now=now)
        observed_speeds.append(sample.speed_kmh)
        now = now + timedelta(seconds=1)
        ticks += 1
        if ticks > 5000:
            break

    assert observed_speeds, "expected at least one telemetry sample"
    assert runner.trip.status == TripStatus.COMPLETED

    expected_peak = max(observed_speeds)
    assert runner.trip.maximum_speed_kmh == expected_peak, (
        "trip maximum_speed_kmh must equal the observed telemetry peak, "
        f"got {runner.trip.maximum_speed_kmh}, expected {expected_peak}"
    )
    assert runner.trip.maximum_speed_kmh > 0.0
