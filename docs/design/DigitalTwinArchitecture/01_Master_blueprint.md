# DriveVitals — Digital Twin Architecture

## 1. Vision

DriveVitals models a fleet as a living system, not a set of independent vehicle simulators. A Digital Twin of a fleet means:

- Drivers make decisions under real constraints (fatigue, cargo, road conditions).
- Vehicles respond physically to those decisions (throttle, braking, gear, wear).
- Trips are executed over time, not generated instantaneously.
- Maintenance accumulates as a consequence of usage, not as a scripted event.
- Telemetry is an **output** of simulated reality, never an input assumption.
- Analytics derive intelligence from what actually happened in the twin, the same way they would from a real fleet's historical data.

This is the core design philosophy: **reality over randomness**. Randomness (noise, variance, environmental effects) is used to make individual signals realistic, but it never drives system-level outcomes. Outcomes are driven by state and decisions; randomness only perturbs them.

## 2. Design Principles

| Principle | Meaning |
|---|---|
| Persistent fleet state | The fleet's condition (vehicle health, fuel, driver fatigue, trip history) persists across ticks and sessions — it is not regenerated per request. |
| Fleet-centric simulation | The unit of simulation is the fleet, not a single vehicle. Vehicles exist inside a shared clock, shared environment, and shared dispatch logic. |
| Relationship-based intelligence | Insight comes from relationships between entities (this driver + this vehicle + this route + this cargo), not from isolated vehicle metrics. |
| Modular architecture | Each layer has one job and communicates through well-defined interfaces (events, intents, state snapshots), so layers can be replaced independently (e.g. swap the physics engine, or swap simulated sensors for real OBD-II). |
| Determinism by default | Given the same seed and configuration, the same run must be reproducible (see Simulation Engine Design doc). |

## 3. System Layers

### 3.1 Operational Layer
Owns the "business" of the fleet: Fleet, Drivers, Vehicles, Dispatch, Trips, Shifts, Maintenance records. This layer answers "what exists and who is assigned to what."

### 3.2 Decision Layer
The Driver Behaviour Model. Consumes the driver's profile, fatigue state, environment, and current trip context, and produces **intentions**: target speed, throttle request, brake request, steering request. It never touches vehicle state directly.

### 3.3 Physical Simulation Layer
Vehicle Controller + Physics Engine. Converts driver intentions into actual vehicle behaviour: movement, powertrain response, fuel burn, mechanical wear. Physics never decides — it only responds to controller input plus environment.

### 3.4 Data Layer
Sensor Abstraction Layer + Telemetry Pipeline. Reads vehicle state and produces telemetry packets in a fixed schema, regardless of whether the state came from simulation or a real ECU.

### 3.5 Intelligence Layer
Analytics Engine + ML models. Consumes telemetry and events to produce driver scores, vehicle health indices, fuel efficiency metrics, predictive maintenance flags.

## 4. High-Level Architecture Flow

```
Environment ──┐
              ▼
        Fleet Operations (Dispatch, Trip assignment)
              │
              ▼
        Driver Behaviour (Decision Layer)
              │  intentions
              ▼
        Vehicle Controller
              │  actuation
              ▼
        Physics Engine ──► Vehicle State
                                │
                                ▼
                    Sensor Abstraction Layer
                                │
                                ▼
                        Telemetry Pipeline
                                │
                     ┌──────────┴──────────┐
                     ▼                     ▼
              Analytics Engine        Persistence (DB)
                     │                     │
                     └─────────┬───────────┘
                                ▼
                            Dashboard
```

This is the **conceptual** flow. The **execution-order** flow (what actually runs each tick) is defined precisely in `03-simulation-engine-design.md` — this document intentionally does not fix scheduling, since that is a runtime concern, not an architectural one.

## 5. Scalability Strategy (summary)

DriveVitals is designed to run up to 500 vehicles concurrently within one fleet simulation. The architecture achieves this through:

- A **Vehicle Manager** that owns the collection of vehicle entities and batches their updates (see `03-simulation-engine-design.md`).
- **Selective telemetry streaming**: not every tick's full state is pushed to the dashboard; only deltas or sampled snapshots are streamed to clients, while full-resolution data is persisted for analytics.
- **Stateless workers** for physics/decision computation so the update cycle can be parallelized across vehicles if needed later.

Full detail lives in `03-simulation-engine-design.md` (execution model) and `06-integration-deployment-architecture.md` (infrastructure/database scaling).

## 6. Integration Strategy (summary)

The Sensor Abstraction Layer guarantees that a **Digital Twin Vehicle** (simulated) and a **real vehicle** (OBD-II/CAN) produce telemetry in an identical schema. Everything downstream of telemetry (pipeline, analytics, dashboard) is source-agnostic. Full detail lives in `06-integration-deployment-architecture.md`.

## 7. What This Document Deliberately Excludes

To keep this document at the "architecture" level rather than duplicating detail:
- Object-level responsibilities and ownership → `02-digital-twin-object-model.md`
- Tick lifecycle, scheduler, determinism → `03-simulation-engine-design.md`
- Vehicle physics/powertrain/fuel/wear detail → `04-vehicle-simulation-model.md`
- Telemetry schema and analytics detail → `05-data-and-intelligence-architecture.md`
- Deployment/database/OBD-II integration detail → `06-integration-deployment-architecture.md`