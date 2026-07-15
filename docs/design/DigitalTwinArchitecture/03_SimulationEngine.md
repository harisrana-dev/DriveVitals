# DriveVitals — Simulation Engine Design

This document fixes **Problem 2 (runtime execution model)**, **Problem 3 (500-vehicle scalability)**, and **Problem 4 (determinism)**.

## 1. Digital Twin Runtime

The Runtime owns three things only: the simulation clock, the module registry, and the tick sequence. It contains no business logic — it calls each registered module in a fixed order and passes it the current tick context.

```python
class TickContext:
    tick_id: int
    sim_time: datetime
    dt: float           # seconds per tick
    rng: RandomState     # seeded, per-tick derived stream
```

## 2. Tick Lifecycle

Each tick executes in this strict order:

```
1. Clock Update           → advance sim_time by dt, produce TickContext
2. Environment Update      → weather/traffic/road conditions for this tick
3. Operational Events      → Dispatch resolves assignments, Shift/Trip lifecycle events
4. Driver Decisions        → Decision Layer produces DriverIntent per active vehicle
5. Vehicle Controller      → intent + constraints → actuation
6. Physics Update          → actuation + environment + cargo → next Vehicle State
7. Maintenance Accrual     → wear deltas applied, thresholds checked → MaintenanceDue events
8. Sensor Sampling         → Vehicle State → Telemetry Packet (per sensor sample rate)
9. Telemetry Emission      → packets pushed to Telemetry Pipeline
10. Analytics Update       → incremental analytics consume this tick's telemetry/events
11. Persistence            → batched writes to DB
12. Dashboard Streaming    → selective/sampled push to connected clients
```

Steps 2–9 run **per vehicle**, but the ordering across steps is fixed for every vehicle before moving to the next step (i.e. the Runtime does 3→4→5→6→7→8→9 for all vehicles in step-major order, not vehicle-major order). This matters for determinism: it means the RNG draw sequence is stable regardless of how vehicles are batched or parallelized, since each step consumes a per-vehicle-per-tick derived seed rather than a shared global stream.

## 3. Scheduler

The Runtime does not iterate vehicles directly — it delegates to the **Vehicle Manager**:

```
DigitalTwinRuntime
      │
      ▼
 VehicleManager.update(tick_context)
      │
      ├── batches vehicles (e.g. chunks of 50)
      ├── for each batch: run steps 4–9 (steps 2–3 and 10–12 are fleet-level, not per-batch)
      └── returns aggregated events for step 7/10 consumption
```

The Vehicle Manager is the only object that knows how many vehicles exist and how they're partitioned. This isolates "how do we scale to 500 vehicles" from every other layer — none of them need to know whether they're being called for 1 vehicle or 500.

## 4. Scalability Design (500 Vehicles)

```
Simulation Runtime
        │
        ▼
  Vehicle Manager  ──── Entity Registry (id → entity refs, O(1) lookup)
        │
        ├── Batch 1: Vehicle 001 – 050
        ├── Batch 2: Vehicle 051 – 100
        ├── ...
        └── Batch 10: Vehicle 451 – 500
```

Key mechanisms:

- **Entity Registry**: a flat id-indexed store for Vehicle/Driver/Trip lookups, avoiding repeated graph traversal through Fleet each tick.
- **Batched, parallelizable updates**: each batch's steps 4–9 have no cross-vehicle dependency (vehicles don't read each other's state, except indirectly via shared Environment, which is read-only within a tick), so batches can run concurrently (threads/async tasks/workers) without coordination overhead.
- **Selective telemetry streaming**: full-resolution telemetry (every tick, every PID) is persisted to the database for analytics, but the Dashboard only receives a sampled/delta stream (e.g. 1 update/sec/vehicle, or only-on-change fields) to keep the client-facing bandwidth flat regardless of fleet size.
- **Tiered analytics**: cheap per-tick aggregates (fleet-wide averages, active-vehicle counts) update every tick; expensive per-vehicle scoring (driver score, predictive maintenance) runs on a slower cadence (e.g. every N ticks or trip-end) rather than every tick for every vehicle.

## 5. Determinism

Requirement: identical `(seed, fleet_config, driver_configs, route_configs)` must produce an identical run, byte-for-byte, for testing and replay.

Mechanisms:

- **Single root seed** for the simulation run, stored in the run's `SimulationConfig`.
- **Per-entity, per-tick derived seeds**: rather than drawing from one shared RNG (which is order-dependent and breaks under parallel batches), each vehicle/driver derives its own RNG stream per tick as a deterministic hash of `(root_seed, entity_id, tick_id)`. This guarantees the same vehicle gets the same random draws regardless of batch scheduling or thread order.
- **SimulationConfig** is itself a first-class, serializable object: root seed, dt, vehicle roster, driver archetypes, route assignments, environment script/seed. A run is fully reproducible from its config alone.
- **Replay capability**: because Telemetry + Events are persisted per tick, a run can be replayed either by (a) re-executing the simulation from the same `SimulationConfig` (true determinism check), or (b) replaying the persisted telemetry/event stream for dashboard playback without re-simulating.
- **Testing support**: unit tests fix a small `SimulationConfig` (e.g. 1 vehicle, 100 ticks, fixed seed) and assert exact output snapshots — this is how physics/behaviour regressions (e.g. the low-speed gear-reset bug) get caught going forward.

## 6. Summary Table

| Concern | Mechanism |
|---|---|
| Coordination without business logic | Runtime calls modules in fixed tick order only |
| Fleet scale (500 vehicles) | Vehicle Manager + Entity Registry + batching |
| Selective streaming | Full telemetry persisted; sampled/delta stream to dashboard |
| Determinism | Root seed + per-entity-per-tick derived seeds |
| Reproducibility | SimulationConfig as a serializable, complete run spec |
| Regression safety | Fixed-seed unit tests with snapshot assertions |