# DriveVitals — Digital Twin Object Model

This document fixes **Problem 1 (too many responsibilities inside objects)**. Every entity below has exactly one of three roles with respect to any piece of state:

- **Owner** — the only object allowed to hold this state.
- **Updater** — the only object allowed to mutate it (may or may not be the owner).
- **Consumer** — reads it, never mutates it.

State is never mutated by an object that is neither its owner nor its designated updater. All cross-object communication happens through **intents** (requests to change something) or **events** (notifications that something changed), never through direct field mutation of another object.

## 1. Ownership Matrix

| Entity | Owns (state) | Updated by | Consumed by |
|---|---|---|---|
| Fleet | Vehicle registry, Driver registry, Trip registry, Shift registry | Dispatch, Vehicle Manager | Analytics, Dashboard |
| Driver | Profile, Behaviour profile, Fatigue state, Performance history | Driver Behaviour Model (fatigue/perf only — profile is static) | Decision Layer, Analytics |
| Vehicle | Specification (static), State (dynamic), Health, Fuel state, current Driver ref, current Trip ref | Vehicle Controller + Physics Engine (state/health/fuel), Dispatch (driver/trip refs) | Sensor Layer, Analytics, Maintenance |
| Trip | Driver ref, Vehicle ref, Route, Cargo, Telemetry session ref, Event log | Dispatch (creation), Trip Runtime (progress/completion) | Analytics, Dashboard |
| Dispatch | Assignment records | Dispatch service itself | Fleet, Trip |
| Maintenance | Wear thresholds, service history, prediction flags | Maintenance service (reads Vehicle Health, writes its own records) | Fleet, Dashboard |
| Environment | Weather, traffic, road conditions, time, speed limits | Environment service (scripted or procedural) | Decision Layer, Physics Engine |
| Digital Twin Runtime | Simulation clock, module registry, tick sequencing | Runtime itself only | Every layer (reads clock) |

**Key rule:** the Vehicle never generates telemetry directly, and the Driver never touches Vehicle State directly. Both interactions are mediated (Driver → intents → Vehicle Controller; Vehicle State → Sensor Layer → Telemetry).

## 2. Entities

### 2.1 Digital Twin Runtime
Coordinates only — contains zero business logic. Owns the clock and the tick sequence (defined in `03-simulation-engine-design.md`). It calls into each layer in order and passes the current tick number/timestamp; it does not know *what* a Driver Behaviour Model computes, only *when* to call it.

### 2.2 Fleet
Represents the fleet company. Owns the registries (collections) of Vehicles, Drivers, Trips, Shifts, Dispatch records, Maintenance records. Responsible for fleet-level aggregate state (e.g. "vehicles currently active") but does not compute physics or decisions itself — it delegates to the Vehicle Manager and Dispatch.

### 2.3 Driver
Represents a professional operator. Owns Profile (static), Behaviour Profile (aggressive/normal/cautious archetype), Fatigue State, Performance History. Produces **intents**, never touches telemetry or vehicle state:

```
DriverIntent {
  target_speed
  throttle_request
  brake_request
  steering_request
}
```

Fatigue State is updated by the Driver Behaviour Model each tick as a function of shift duration, time of day, and driving intensity — not by the Vehicle or Physics Engine.

### 2.4 Vehicle
Represents a physical asset. Owns Specification (immutable), State (speed, RPM, gear, fuel level, temperature, engine load, battery voltage, odometer, engine hours), Health, Fuel State, and references to its current Driver and Trip. The Vehicle Controller and Physics Engine are the only updaters of State/Health/Fuel; Dispatch is the only updater of the Driver/Trip references.

### 2.5 Vehicle Controller
Sits between intention and physics. Takes a `DriverIntent` + current Vehicle State + Vehicle Specification and produces **actuation values** (actual throttle %, actual brake %, gear-shift decision) after applying vehicle constraints (e.g. can't exceed rated RPM, transmission logic, traction limits). This is where "the driver wants X but the vehicle can only do Y" is resolved.

### 2.6 Physics Engine
Pure function of (actuation values, current State, Environment, Cargo) → next State. Never decides, only responds. Computes acceleration, speed, RPM, gear behaviour outcome, fuel consumption, mechanical wear delta.

### 2.7 Trip
Represents one transportation operation. Owns Driver ref, Vehicle ref, Route, Cargo, Telemetry session ref, and its own Event log (trip started, delay, stop, completed). Trip Runtime updates trip progress based on Vehicle State (position/odometer) — Trip does not push state onto the Vehicle.

### 2.8 Route
Static-per-trip data: road segments, distance, speed limits, traffic zones, gradient. Consumed by Environment and Decision Layer.

### 2.9 Cargo
Weight, type, priority, handling requirements. Consumed by Physics Engine (affects acceleration/braking/fuel) and Decision Layer (affects target speed choices, e.g. fragile cargo → smoother driving).

### 2.10 Shift
A driver's working period: hours, breaks, trip history. Updated by the Dispatch/Scheduling service, consumed by the Driver Behaviour Model to compute fatigue.

### 2.11 Dispatch
A service, not passive data. Responsible for driver assignment, vehicle assignment, trip creation, fleet utilization. It is the only writer of Vehicle.current_driver, Vehicle.current_trip, and Trip creation records.

### 2.12 Maintenance
A service that reads Vehicle Health/wear accumulation and writes its own records: inspections, wear tracking, service history, maintenance prediction. It never mutates Vehicle State directly — if maintenance forces a vehicle offline, it does so via an event consumed by Dispatch/Fleet, not by direct mutation.

### 2.13 Environment
Weather, traffic, road conditions, gradient, time, speed limits. An external-to-vehicle context object, updated by an Environment service on its own schedule (can be scripted, seeded-random, or eventually pulled from a real weather/traffic API).

### 2.14 Sensor Abstraction Layer
Purpose: enable real-vehicle integration without touching anything downstream. Simulation path: Vehicle Physics → Virtual Sensor Provider → Telemetry Packet. Future real path: Vehicle ECU → OBD-II Provider → Telemetry Packet. Both providers implement the same interface and emit the same schema (see `05-data-and-intelligence-architecture.md`).

## 3. Event System

Because Runtime coordinates only, cross-layer notifications happen via events, not direct calls upward. Examples:

| Event | Emitted by | Consumed by |
|---|---|---|
| `TripCompleted` | Trip Runtime | Fleet, Dispatch, Analytics |
| `MaintenanceDue` | Maintenance | Dispatch, Fleet, Dashboard |
| `VehicleFault` | Physics Engine / Vehicle | Maintenance, Dashboard, Analytics |
| `DriverFatigueCritical` | Driver Behaviour Model | Dispatch (may force a break/reassignment) |
| `TelemetryEmitted` | Sensor Abstraction Layer | Telemetry Pipeline |

Events are append-only per tick and consumed within the same tick or the next, per the ordering defined in `03-simulation-engine-design.md`. No entity subscribes to another entity's raw state — only to its events or through the Runtime's read-only snapshot API.