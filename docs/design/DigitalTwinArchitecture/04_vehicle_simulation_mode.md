# DriveVitals — Vehicle Simulation Model

This document details the Physical Simulation Layer referenced in `01-digital-twin-architecture.md` and `02-digital-twin-object-model.md`: how a `DriverIntent` becomes an updated `VehicleState`.

## 1. Vehicle Specification (static)

```
VehicleSpecification {
  manufacturer, model, vehicle_type
  engine_size, fuel_type, transmission_type
  weight, payload_capacity, fuel_capacity
  torque_curve, gear_ratios[], max_rpm
}
```

Vehicle type (city car / aggressive-profile car / highway truck / delivery van) selects which archetype parameters apply, matching the four existing simulator archetypes already implemented (city, aggressive, highway, delivery van).

## 2. Vehicle State (dynamic)

```
VehicleState {
  speed, rpm, gear, fuel_level
  coolant_temp, engine_load, battery_voltage
  odometer, engine_hours
  health_flags: { stale, fault_codes[] }
}
```

## 3. Vehicle Controller

Input: `DriverIntent` (target speed, throttle request, brake request, steering request) + current `VehicleState` + `VehicleSpecification` + `Environment`.

Responsibilities:
1. **Throttle/brake shaping** — clamp requested throttle/brake to what's physically achievable given current gear and RPM (prevents unrealistic instant jumps).
2. **Transmission logic** — a gear-shift state machine decides up-shift/down-shift based on RPM band, load, and target speed, rather than instantaneously snapping to an "ideal" gear. This is where the previously-fixed low-speed gear-reset bug is guarded against: the state machine only resets to neutral/first gear below an explicit stop-threshold speed, not on any low-RPM reading.
3. **Constraint enforcement** — max RPM, traction limits under wet/icy Environment conditions, load-dependent braking distance.

Output: `ActuationValues { throttle_pct, brake_pct, gear, steering_angle }` — passed to the Physics Engine.

## 4. Physics Engine

Pure function: `(ActuationValues, VehicleState, Environment, Cargo) → VehicleState'`. Never makes decisions, only computes outcomes.

### 4.1 Powertrain / Acceleration
Uses the specification's torque curve at current RPM/gear to compute available force, minus drag (speed-dependent) and rolling resistance (cargo-weight-dependent), to produce acceleration and next speed/RPM.

### 4.2 Fuel Model
Torque-curve-based consumption: fuel burn rate is a function of engine load and RPM (not simply speed), so idling, heavy acceleration, and highway cruise all draw fuel differently — matching the existing torque-curve fuel model already built for the simulators.

### 4.3 Noise / Realism
An Ornstein-Uhlenbeck process is applied to sensor-level signals (e.g. small RPM jitter, temperature drift) so telemetry looks like real noisy sensor data — but this noise is applied **after** the deterministic physics computation, never used to decide outcomes like speed or gear (keeps physics reality-driven, not randomness-driven, per the core design philosophy in doc 1).

### 4.4 Thermal Model
Coolant temperature follows a warm-up curve from cold start toward operating temperature, asymptotically, rather than jumping — this is the fix applied after soak testing caught instant-warm-up as unrealistic.

### 4.5 Mechanical Wear
Wear accumulates as a function of engine hours, load history, and harsh-event counts (hard braking, hard acceleration) rather than pure odometer distance. Wear deltas are exposed to the Maintenance service via `VehicleState.health_flags` and dedicated wear counters, not computed by Maintenance itself (Physics Engine is the sole updater of wear state; Maintenance only reads it and decides service actions).

### 4.6 Car-Following / Traffic Model
For non-solo driving contexts (e.g. highway fleet vans), a car-following model (e.g. IDM-style) adjusts target speed relative to a lead vehicle/traffic density from Environment, feeding back into the Decision Layer's next-tick target speed rather than being computed inside Physics directly — Physics only executes the resulting intent.

## 5. Health & Fault State

`health_flags.stale` guards against a previously-fixed bug where sensor values could remain "stuck" during periods with no state change (e.g. parked/idle) — the Sensor Abstraction Layer explicitly marks a reading stale rather than silently repeating the last value, so Analytics/Dashboard can distinguish "no change" from "no data."

`fault_codes[]` are emitted as discrete events (`VehicleFault`) when thresholds are crossed (e.g. overheat, low oil pressure proxy), consumed by Maintenance and Dashboard.

## 6. Interface Contract

The Vehicle Simulation Model's only external outputs are:
- `VehicleState` (read by Sensor Abstraction Layer)
- `VehicleFault` / `MaintenanceDue`-triggering wear events (read by Maintenance)

It never emits telemetry directly and never reads Driver internals directly — all driver influence arrives strictly as `DriverIntent`, keeping this layer swappable and testable in isolation (a prerequisite for the deterministic unit tests described in `03-simulation-engine-design.md`).