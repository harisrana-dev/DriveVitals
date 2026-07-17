"""PhysicsEngine: orchestrator for the Physics Engine layer.

Reads `Vehicle` (and its `VehicleSpecification`), the `VehicleActuation`
produced by the Vehicle Controller, the current `EnvironmentSnapshot`,
and the `TickContext`, and updates `vehicle.state` in place. This is
the pipeline stage positioned after the Vehicle Controller and before
the (future) Sensor Layer. Physics never decides, plans, dispatches, or
generates telemetry -- it only evolves already-commanded physical
state forward by one tick.

===========================================================================
INTERFACE MISMATCH REPORT (per the brief's instruction to report rather
than silently patch around gaps in modules this sprint cannot modify)
===========================================================================

The brief's "VehicleState Ownership" list names several fields that do
not exist, under those names, on the actual
`digital_twin.entities.vehicle.VehicleState` (Sprint 2, unmodified):

    Brief's name          | Actual VehicleState field (or "none")
    -----------------------|--------------------------------------
    current_speed          | current_speed_kmh                 (name differs only)
    acceleration            | NOT PRESENT
    rpm                     | current_rpm                       (name differs only)
    engine_load             | engine_load_percent                (name differs only)
    gear                    | current_gear                       (name differs only)
    distance                | NOT PRESENT (only cumulative odometer_km exists)
    odometer                | odometer_km                        (name differs only)
    fuel_level              | fuel_level_percent                 (name differs only)
    fuel_consumed            | NOT PRESENT (no cumulative consumption field)
    coolant_temperature      | NOT PRESENT (only engine_temperature_celsius exists)
    engine_temperature       | engine_temperature_celsius          (name differs only)
    tyre_health              | tyre_wear_percent                  (inverse convention: wear, not health)
    brake_pad_health         | brake_wear_percent                 (inverse convention: wear, not health)
    oil_life                 | NOT PRESENT

Resolution applied (no existing file modified, per instructions):
    - Fields that merely differ in name are written to their real
      field (e.g. `acceleration` -> computed and applied to
      `current_speed_kmh` via Kinematics; RPM/engine_load/gear/
      fuel_level/odometer/engine_temperature all map directly).
    - `tyre_health`/`brake_pad_health` are modeled as their existing
      wear-percentage counterparts (`tyre_wear_percent`,
      `brake_wear_percent`); "wear" and "health" are complementary
      (health = 100 - wear), so no information is lost, only the sign
      convention differs from the brief's wording.
    - `acceleration`, `distance` (this tick), `fuel_consumed` (this
      tick), and `oil_life` have nowhere to persist on `VehicleState`.
      They are still computed every tick and returned via
      `PhysicsTickResult` (see below) rather than silently dropped, so
      the values are available to callers today. `oil_life_percent`
      additionally has no persisted home at all, so callers must
      thread `previous_oil_life_percent` through themselves across
      ticks if they want continuity (see `update()`'s docstring).
    - Recommended fix for a future sprint: extend `VehicleState` with
      `distance_this_tick_km` (or leave distance-derivation to
      callers via odometer deltas, as `PhysicsTickResult` already
      does), `fuel_consumed_liters` (cumulative), and
      `oil_life_percent`, and rename `tyre_wear_percent`/
      `brake_wear_percent` to `*_health_percent` if "health" framing
      is preferred fleet-wide -- or simply update the brief's field
      list to match the wear-based convention already in place.

Separately, `VehicleSpecification` has no mass, drag coefficient,
frontal area, tank capacity, or RPM range -- see the longer note in
`physics_constants.py`. This engine uses fleet-wide default physical
constants from that module for every vehicle until a future sprint
supplies real per-vehicle values.
"""

from __future__ import annotations

from dataclasses import dataclass

from digital_twin.controller.vehicle_actuation import VehicleActuation
from digital_twin.entities.environment import EnvironmentSnapshot
from digital_twin.entities.vehicle import Vehicle
from digital_twin.physics import physics_constants as const
from digital_twin.physics.dynamics import Dynamics
from digital_twin.physics.fuel_model import FuelModel
from digital_twin.physics.kinematics import Kinematics
from digital_twin.physics.powertrain import Powertrain
from digital_twin.physics.resistance_model import ResistanceModel
from digital_twin.physics.thermal_model import ThermalModel
from digital_twin.physics.wear_model import WearModel
from digital_twin.runtime.tick_context import TickContext


@dataclass(frozen=True)
class PhysicsTickResult:
    """Auxiliary values computed this tick that have no home on VehicleState.

    `PhysicsEngine.update()` mutates `vehicle.state` in place for every
    field that has a real counterpart there; this result carries the
    handful of values the interface mismatch report above identifies as
    not currently persistable, plus a couple of useful derived metrics,
    so they are not silently discarded.

    Attributes:
        acceleration_mps2: Net acceleration applied this tick.
        distance_travelled_km: Distance travelled this tick (the delta
            already folded into `vehicle.state.odometer_km`).
        average_speed_kmh: Average speed over this tick.
        fuel_consumed_liters: Fuel/energy consumed this tick.
        remaining_range_km: Estimated remaining range at this tick's
            fuel level and consumption rate.
        oil_life_percent: Updated oil life; not persisted anywhere on
            `VehicleState` (see interface mismatch report). Callers
            wanting continuity must pass this back in as
            `previous_oil_life_percent` on the next call.
        is_overheating: Whether the engine is currently overheating.
    """

    acceleration_mps2: float
    distance_travelled_km: float
    average_speed_kmh: float
    fuel_consumed_liters: float
    remaining_range_km: float
    oil_life_percent: float
    is_overheating: bool


class PhysicsEngine:
    """Evolves a Vehicle's physical state forward by one tick.

    Depends on `Kinematics`, `Dynamics`, `Powertrain`, `ResistanceModel`,
    `FuelModel`, `ThermalModel`, and `WearModel`, each independently
    injectable so the engine is testable with fakes and each submodel
    is independently testable in isolation.
    """

    def __init__(
        self,
        kinematics: Kinematics | None = None,
        dynamics: Dynamics | None = None,
        powertrain: Powertrain | None = None,
        resistance_model: ResistanceModel | None = None,
        fuel_model: FuelModel | None = None,
        thermal_model: ThermalModel | None = None,
        wear_model: WearModel | None = None,
    ) -> None:
        """Initialize the engine, defaulting to the standard submodel set.

        Args:
            kinematics: Speed/distance/odometer integrator. Defaults to
                a new `Kinematics`.
            dynamics: Net acceleration computer. Defaults to a new
                `Dynamics`.
            powertrain: RPM/engine-load/gear-confirmation computer.
                Defaults to a new `Powertrain`.
            resistance_model: Resistive force / traction computer.
                Defaults to a new `ResistanceModel`.
            fuel_model: Fuel/energy consumption computer. Defaults to a
                new `FuelModel`.
            thermal_model: Engine temperature computer. Defaults to a
                new `ThermalModel`.
            wear_model: Tyre/brake/engine/oil wear computer. Defaults to
                a new `WearModel`.
        """
        self._resistance_model = resistance_model or ResistanceModel()
        self._kinematics = kinematics or Kinematics()
        self._dynamics = dynamics or Dynamics(resistance_model=self._resistance_model)
        self._powertrain = powertrain or Powertrain()
        self._fuel_model = fuel_model or FuelModel()
        self._thermal_model = thermal_model or ThermalModel()
        self._wear_model = wear_model or WearModel()

    def update(
        self,
        vehicle: Vehicle,
        actuation: VehicleActuation,
        environment: EnvironmentSnapshot,
        tick_context: TickContext,
        previous_oil_life_percent: float = 100.0,
    ) -> PhysicsTickResult:
        """Evolve `vehicle.state` forward by one tick, in place.

        Args:
            vehicle: The vehicle to evolve. `vehicle.state` is mutated
                directly; `vehicle.specification` is read only.
            actuation: The commanded throttle/brake/gear/clutch state
                from the Vehicle Controller for this tick.
            environment: Current environmental conditions, used for
                traction/grip and ambient temperature.
            tick_context: The simulation's immutable per-tick context;
                `delta_time` drives every integration this tick.
            previous_oil_life_percent: Oil life carried over from the
                previous tick's `PhysicsTickResult.oil_life_percent`
                (defaults to 100.0, i.e. fresh oil, for a vehicle's
                first tick). See the interface mismatch report above
                for why this can't simply be read off `vehicle.state`.

        Returns:
            A PhysicsTickResult with the tick's auxiliary values that
            have no home on `VehicleState` (see interface mismatch
            report above). `vehicle.state` itself has already been
            updated by the time this returns.
        """
        state = vehicle.state
        delta_time_seconds = tick_context.delta_time

        traction_factor = self._resistance_model.compute_traction_factor(environment)

        acceleration_mps2 = self._dynamics.compute_acceleration_mps2(
            actuation=actuation,
            current_speed_kmh=state.current_speed_kmh,
            mass_kg=const.DEFAULT_VEHICLE_MASS_KG,
            traction_factor=traction_factor,
        )

        speed_before_kmh = state.current_speed_kmh
        new_speed_kmh = self._kinematics.update_speed_kmh(
            current_speed_kmh=speed_before_kmh,
            acceleration_mps2=acceleration_mps2,
            delta_time_seconds=delta_time_seconds,
        )
        average_speed_kmh = self._kinematics.compute_average_speed_kmh(
            speed_before_kmh, new_speed_kmh
        )
        distance_travelled_km = self._kinematics.compute_distance_travelled_km(
            average_speed_kmh, delta_time_seconds
        )
        new_odometer_km = self._kinematics.update_odometer_km(
            state.odometer_km, distance_travelled_km
        )

        confirmed_gear = self._powertrain.confirm_gear(actuation.requested_gear)
        target_rpm = self._powertrain.compute_target_rpm(
            current_speed_kmh=new_speed_kmh,
            requested_gear=actuation.requested_gear,
            clutch_engaged=actuation.clutch_engaged,
            throttle_percentage=actuation.throttle_percentage,
        )
        new_rpm = self._powertrain.update_rpm(
            current_rpm=state.current_rpm,
            target_rpm=target_rpm,
            delta_time_seconds=delta_time_seconds,
        )
        new_engine_load_percent = self._powertrain.compute_engine_load_percent(
            throttle_percentage=actuation.throttle_percentage,
            current_rpm=new_rpm,
        )

        fuel_rate_l_per_hour = self._fuel_model.compute_fuel_rate_l_per_hour(
            rpm=new_rpm,
            throttle_percentage=actuation.throttle_percentage,
            engine_load_percent=new_engine_load_percent,
            fuel_type=vehicle.specification.fuel_type,
        )
        fuel_consumed_liters = self._fuel_model.compute_fuel_consumed_liters(
            fuel_rate_l_per_hour, delta_time_seconds
        )
        new_fuel_level_percent = self._fuel_model.update_fuel_level_percent(
            current_fuel_percent=state.fuel_level_percent,
            fuel_consumed_liters=fuel_consumed_liters,
        )
        consumption_l_per_100km = (
            (fuel_consumed_liters / distance_travelled_km) * 100.0
            if distance_travelled_km > 1e-6
            else (fuel_rate_l_per_hour / max(new_speed_kmh, 1.0)) * 100.0
        )
        remaining_range_km = self._fuel_model.estimate_remaining_range_km(
            fuel_level_percent=new_fuel_level_percent,
            tank_capacity_liters=const.DEFAULT_TANK_CAPACITY_LITERS,
            average_consumption_l_per_100km=consumption_l_per_100km,
        )

        target_temperature_c = self._thermal_model.compute_target_temperature_c(
            engine_load_percent=new_engine_load_percent,
            rpm=new_rpm,
            ambient_temperature_c=environment.temperature_celsius,
        )
        new_engine_temperature_c = self._thermal_model.update_temperature_c(
            current_temperature_c=state.engine_temperature_celsius,
            target_temperature_c=target_temperature_c,
            delta_time_seconds=delta_time_seconds,
        )
        is_overheating = self._thermal_model.is_overheating(new_engine_temperature_c)

        new_tyre_wear_percent = self._wear_model.update_tyre_wear_percent(
            current_tyre_wear_percent=state.tyre_wear_percent,
            distance_travelled_km=distance_travelled_km,
            average_speed_kmh=average_speed_kmh,
            traction_factor=traction_factor,
        )
        new_brake_wear_percent = self._wear_model.update_brake_wear_percent(
            current_brake_wear_percent=state.brake_wear_percent,
            brake_percentage=actuation.brake_percentage,
            current_speed_kmh=speed_before_kmh,
            delta_time_seconds=delta_time_seconds,
        )
        new_engine_health_percent = self._wear_model.update_engine_health_percent(
            current_engine_health_percent=state.engine_health_percent,
            engine_temperature_c=new_engine_temperature_c,
            delta_time_seconds=delta_time_seconds,
        )
        new_oil_life_percent = self._wear_model.compute_oil_life_percent(
            previous_oil_life_percent=previous_oil_life_percent,
            delta_time_seconds=delta_time_seconds,
            engine_load_percent=new_engine_load_percent,
        )

        new_engine_hours = state.engine_hours + (delta_time_seconds / 3600.0)
        new_health_score = self._compute_composite_health_score(
            engine_health_percent=new_engine_health_percent,
            tyre_wear_percent=new_tyre_wear_percent,
            brake_wear_percent=new_brake_wear_percent,
        )

        # Apply every update to the real VehicleState fields in place --
        # Physics is the only module allowed to write these.
        state.current_speed_kmh = new_speed_kmh
        state.current_gear = confirmed_gear
        state.current_rpm = new_rpm
        state.engine_load_percent = new_engine_load_percent
        state.fuel_level_percent = new_fuel_level_percent
        state.engine_temperature_celsius = new_engine_temperature_c
        state.tyre_wear_percent = new_tyre_wear_percent
        state.brake_wear_percent = new_brake_wear_percent
        state.engine_health_percent = new_engine_health_percent
        state.odometer_km = new_odometer_km
        state.engine_hours = new_engine_hours
        state.health_score = new_health_score

        return PhysicsTickResult(
            acceleration_mps2=acceleration_mps2,
            distance_travelled_km=distance_travelled_km,
            average_speed_kmh=average_speed_kmh,
            fuel_consumed_liters=fuel_consumed_liters,
            remaining_range_km=remaining_range_km,
            oil_life_percent=new_oil_life_percent,
            is_overheating=is_overheating,
        )

    def _compute_composite_health_score(
        self,
        engine_health_percent: float,
        tyre_wear_percent: float,
        brake_wear_percent: float,
    ) -> float:
        """Compute the composite `VehicleState.health_score`.

        Args:
            engine_health_percent: Current engine health, already on
                a 100=perfect scale.
            tyre_wear_percent: Current tyre wear, 0=new to 100=worn.
            brake_wear_percent: Current brake wear, 0=new to 100=worn.

        Returns:
            A weighted composite score, 0.0 to 100.0, giving engine
            health the largest single weight since it's the most
            safety/operability-critical of the three.
        """
        tyre_health_percent = 100.0 - tyre_wear_percent
        brake_health_percent = 100.0 - brake_wear_percent

        composite = (
            0.5 * engine_health_percent
            + 0.25 * tyre_health_percent
            + 0.25 * brake_health_percent
        )
        return max(0.0, min(100.0, composite))