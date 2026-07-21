"""EntityBridge: resolves the Sprint 1 <-> Sprint 2+ data-model gap.

===========================================================================
INTERFACE MISMATCH REPORT (inspected before writing any runner code)
===========================================================================

Sprint 1 (`digital_twin.managers.*`) and Sprint 2+
(`digital_twin.entities.*`, Decision Layer, Vehicle Controller, Physics
Engine, Virtual Sensors, Telemetry) were built against two entirely
separate data models that were never reconciled:

    Sprint 1 (managers)                    | Sprint 2+ (everything downstream)
    ----------------------------------------|-------------------------------------
    VehicleManager -> VehicleRecord          | Vehicle (entities.vehicle), owns
      (vehicle_id, vehicle_type: str,         |   VehicleState (current_speed_kmh,
       status, assigned_driver_id,             |   current_rpm, fuel_level_percent,
       assigned_trip_id, odometer_km)           |   tyre_wear_percent, ...) and
                                                  |   VehicleSpecification
                                                  |   (manufacturer, model, year,
                                                  |   fuel_type, transmission)
    DriverManager -> DriverRecord             | Driver (entities.driver), owns
      (driver_id, name, status,                  |   behaviour_profile, experience_
       assigned_vehicle_id/trip_id,                |   level, fatigue_level,
       continuous_work_hours,                       |   working_hours, safety_score...
       break_remaining_minutes)
    TripManager -> TripRecord                  | Trip (entities.trip), owns
      (trip_id, origin, destination,              |   distance_planned_km, events,
       status, driver_id, vehicle_id)              |   status_history, scores...
    EnvironmentManager -> EnvironmentState      | EnvironmentSnapshot
      (weather, road_condition,                   |   (entities.environment): all of
       active_events)                               |   EnvironmentState's fields
                                                       |   PLUS traffic_density,
                                                       |   road_surface, wind,
                                                       |   visibility_meters,
                                                       |   temperature_celsius,
                                                       |   rain_intensity_mm_per_hour,
                                                       |   simulation_time_multiplier

No field in `VehicleRecord` overlaps enough with `VehicleSpecification`
to "convert" one into the other (a vehicle type *string* is not a
manufacturer/model/year/fuel_type/transmission breakdown), and
`EnvironmentState` is a strict subset of `EnvironmentSnapshot` -- it has
no source data for the fields it lacks.

Affected modules: `managers.vehicle_manager`, `managers.driver_manager`,
`managers.trip_manager`, `managers.environment_manager` on one side;
`entities.vehicle`, `entities.driver`, `entities.trip`,
`entities.environment`, and everything built on them (Decision Layer,
Vehicle Controller, Physics Engine, Sensors, Telemetry) on the other.

Smallest clean integration point (this module): rather than modifying
any frozen manager or entity (both explicitly frozen this sprint), this
module is a pure, additive adapter that:

    1. Constructs a `Vehicle`/`Driver` entity *alongside* (not derived
       from) the `VehicleRecord`/`DriverRecord` Sprint 1 creates, using
       the same id, at fleet setup time -- since the two models don't
       share enough data to convert between them.
    2. Every tick, reads the *real*, actively-updated fields Sprint 1
       does maintain (`DriverRecord.continuous_work_hours`,
       `.break_remaining_minutes`) and surfaces them as the scalar
       inputs `DecisionContext` needs, rather than duplicating
       DriverManager's fatigue-accumulation logic.
    3. Maps `EnvironmentManager.state` (`EnvironmentState`) onto an
       `EnvironmentSnapshot` by copying the two fields that genuinely
       overlap (`weather`, `road_condition`) and leaving every field
       `EnvironmentState` doesn't have at `EnvironmentSnapshot`'s own
       dataclass defaults -- never computing or guessing a value for
       them. This is a data-shape adapter, not a weather calculation.

A future sprint should resolve this properly by either extending
`VehicleRecord`/`DriverRecord` to carry (or reference) their full
entity, or by having `FleetManager.onboard_vehicle`/`onboard_driver`
accept and store a pre-built `Vehicle`/`Driver` entity directly. That
is a real interface change to a frozen module and is explicitly not
done here.
"""

from __future__ import annotations

from digital_twin.common.enums import DriverStatus
from digital_twin.entities.environment import EnvironmentSnapshot
from digital_twin.entities.driver import Driver
from digital_twin.managers.environment_manager import EnvironmentState
from digital_twin.runtime.tick_context import TickContext


def bridge_environment_snapshot(
    environment_state: EnvironmentState, tick_context: TickContext
) -> EnvironmentSnapshot:
    """Map EnvironmentManager's EnvironmentState onto an EnvironmentSnapshot.

    Only `weather` and `road_condition` are copied, since those are the
    only two fields `EnvironmentState` actually models. Every other
    `EnvironmentSnapshot` field (traffic_density, road_surface, wind,
    visibility_meters, temperature_celsius, rain_intensity_mm_per_hour,
    simulation_time_multiplier) is left at its own dataclass default --
    this function never computes or fabricates a value for a signal
    `EnvironmentManager` doesn't produce.

    Args:
        environment_state: The current state from
            `EnvironmentManager.state`.
        tick_context: The current tick's context, used only for
            `current_time` (`EnvironmentSnapshot` requires a
            timestamp; `simulation_time` is the obvious, already-
            available source -- not a new value).

    Returns:
        An EnvironmentSnapshot with `weather`/`road_condition` copied
        from `environment_state` and every other field at its default.
    """
    return EnvironmentSnapshot(
        current_time=tick_context.simulation_time,
        weather=environment_state.weather,
        road_condition=environment_state.road_condition,
    )


def compute_continuous_driving_hours(driver_record: Driver) -> float:
    """Surface DriverManager's real, actively-ticked continuous driving hours.

    Args:
        driver_record: The driver's current record, maintained by
            `DriverManager.on_tick` every tick.

    Returns:
        `driver_record.continuous_work_hours`, unchanged -- this is the
        real accumulator Sprint 1 already maintains, not a duplicate
        computation.
    """
    return driver_record.continuous_work_hours


def compute_break_duration_minutes(
    driver_record: Driver, mandatory_break_minutes: float
) -> float:
    """Derive elapsed break duration from DriverManager's own record.

    `DriverRecord` only tracks *remaining* break time while a driver is
    on break (`break_remaining_minutes`), and resets to 0 once the
    break completes -- it does not retain "how long was my last
    completed break." While a break is in progress, elapsed time is
    exactly `mandatory_break_minutes - break_remaining_minutes`; once
    the break ends, DriverManager itself resets the driver to
    `AVAILABLE` with fresh hours, so there is nothing left to recover
    from and 0.0 is the correct (not fabricated) answer.

    Args:
        driver_record: The driver's current record.
        mandatory_break_minutes: The configured mandatory break
            duration, from `DriverManagerConfig.mandatory_break_minutes`
            (the same configuration DriverManager itself was built
            with), needed to compute elapsed time from remaining time.

    Returns:
        Elapsed break duration in minutes, or 0.0 if the driver is not
        currently on break.
    """
    if driver_record.status != DriverStatus.ON_BREAK:
        return 0.0
    return max(0.0, mandatory_break_minutes - driver_record.break_remaining_minutes)


def compute_shift_duration_hours(tick_context: TickContext) -> float:
    """Derive elapsed shift duration from simulation-elapsed time.

    No `Shift` entity is actively advanced tick-over-tick anywhere in
    the current architecture (`FleetManager.schedule_shift` creates a
    `ShiftRecord`, but nothing ticks its elapsed duration), so there is
    no real per-driver shift-duration accumulator to read. This uses
    total elapsed simulated time since tick 0 as a deterministic proxy
    -- a documented approximation, not a fabricated random value.

    Args:
        tick_context: The current tick's context.

    Returns:
        Elapsed simulated hours since the start of the simulation.
    """
    return (tick_context.tick_id * tick_context.delta_time) / 3600.0