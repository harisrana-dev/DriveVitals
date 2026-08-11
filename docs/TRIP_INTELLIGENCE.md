# DriveVitals — Trip Intelligence Documentation

> **Source of truth:** `backend/fleet/models/trip.py`, `backend/fleet/runtime/vehicle_runner.py`, `backend/fleet/runtime/fleet_runner.py`, `backend/application/runtime.py`, `backend/trips/services/trip_builder.py`, `backend/trips/services/active_trip_builder.py`, `backend/trips/store/trip_store.py`, `backend/trips/schemas/trip_payload.py`.
> This document describes the trip system as implemented today.

---

## 1. Trip Lifecycle

A trip is a state machine with five states:

```text
ASSIGNED
    ↓
STARTED
    ↓
IN_PROGRESS
    ↓
COMPLETED
```

Additionally, stale trips from a previous runtime session transition to:

```text
IN_PROGRESS  (stale)
    ↓
ABORTED
```

### State Transitions

| From | To | Trigger | Where |
|------|----|---------|-------|
| `ASSIGNED` | `STARTED` | `FleetRunner.start_all()` | `vehicle_runner.py:start()` |
| `STARTED` | `IN_PROGRESS` | First `advance(delta_km)` | `trip.py:advance()` |
| `IN_PROGRESS` | `COMPLETED` | `distance_travelled_km >= route.distance_km` | `vehicle_runner.py:tick()` |
| `IN_PROGRESS` | `ABORTED` | Runtime startup `abort_stale_trips()` | `persistence_service.py` |

No other transitions are permitted. Attempting an illegal transition raises `ValueError`.

---

## 2. Trip Creation

Trips are created during `DriveVitalsRuntime._configure_fleet()`:

1. `FleetFactory.from_config()` builds 6 `Vehicle`, 6 `Driver`, 6 `Route`, and 6 `DriverAssignment` instances.
2. For each assignment, a `Trip` is instantiated with a fresh UUID and status `ASSIGNED`.
3. An `AnalyticsContext` is registered in `AnalyticsContextStore`, binding the trip to its route, driver, and vehicle metadata.
4. The vehicle/driver/route/trip quadruple is added to `FleetRunner`.

**Source of truth for trip identity:** `Trip.trip_id` (UUID generated in `_configure_fleet`).

---

## 3. Trip Start

`FleetRunner.start_all(now)` calls `VehicleRunner.start(now)` for every runner:

- `trip.start(starting_odometer_km, at=now)` sets `started_at` and transitions to `STARTED`.
- `vehicle.start_engine()` marks the vehicle as running.
- `runtime_state.reset()` clears per-trip runtime state.

---

## 4. Active-Trip Invariant

At any point during runtime, the set of active trips is exactly the set of `VehicleRunner` instances whose `trip.status` is `STARTED` or `IN_PROGRESS`. This set is computed by `FleetRunner.active_runners()` on every tick and gates the runtime loop.

**Invariant:** `len(active_runners())` is always ≤ the number of fleet assignments. No phantom active trips can exist because a trip only becomes active through `FleetRunner`, and only `VehicleRunner.tick()` can advance or complete it.

---

## 5. Distance Accumulation

Distance is accumulated in `Trip.distance_travelled_km`:

- `VehicleRunner.tick()` calls `self.trip.advance(distance_km)` with the distance advanced this tick.
- `advance()` adds the delta and transitions from `STARTED` → `IN_PROGRESS` on the first call.

**Source of truth:** `Trip.distance_travelled_km` (never the vehicle's lifetime odometer).

---

## 6. Duration Calculation

Duration is calculated at completion time from timestamps:

```python
duration_seconds = int(
    (trip.completed_at - trip.started_at).total_seconds()
)
```

For active trips, duration is computed live as `now - trip.started_at` in `build_active_trip_snapshot()`.

---

## 7. Fuel Consumption Calculation

Fuel used is derived from the vehicle's fuel-level percentage drop:

1. At runtime startup, `_initial_fuel_levels[vehicle_id]` records each vehicle's starting fuel percentage.
2. At trip completion, `final_fuel_pct = runner.vehicle.fuel_level_percent`.
3. `fuel_used_pct = initial_pct - final_pct`.
4. `fuel_used_liters = (fuel_used_pct / 100.0) * 60.0` (assumed tank capacity: 60 L).

The completed `Trip.fuel_used_liters` is updated so both the WebSocket path and the DB path report the same value.

**Source of truth for active trips:** `_live_fuel_consumed()` in `runtime.py`.

---

## 8. Safety Score & Grade

### 8.1 Scoring Formula

The canonical safety score is a distance-normalized exponential decay:

```python
score = SAFETY_START * exp(
    -weighted_density * SAFETY_DENSITY_SENSITIVITY
)
```

Where:

- `SAFETY_START = 100.0`
- `weighted_density = events_per_km(weighted_event_count, distance_km)`
- `weighted_event_count = harsh_braking * 2.0 + aggressive_throttle * 1.5 + speeding * 3.0 + high_rpm * 1.0`
- `SAFETY_DENSITY_SENSITIVITY = 0.35`

The score is clamped to `[0, 100]` and rounded to 2 decimal places.

### 8.2 Grade Mapping

| Score | Grade |
|-------|-------|
| ≥ 90 | A |
| ≥ 80 | B |
| ≥ 70 | C |
| ≥ 60 | D |
| < 60 | F |

**Important:** Safety score and grade are **only computed for completed trips**. Active trips report `safety_score: null` and `grade: null` because the density normalization requires the final trip distance.

---

## 9. Behavioural Event Detection

Events are detected per tick by `DriverBehaviourAnalyzer.analyze()`:

| Event | Trigger |
|-------|---------|
| `speeding` | `speed_kmh > speed_limit_kmh + threshold` |
| `harsh_braking` | `brake_pressure > threshold` while decelerating |
| `aggressive_throttle` | `throttle_position_percent > threshold` with rising speed |
| `high_rpm` | `rpm > threshold` |

Thresholds are configurable in `DriverBehaviourAnalyzer`.

### 9.1 Event Coalescing

`BehaviourEventTracker.process()` converts point-in-time detections into temporal events:

- When a condition becomes true, a new event starts.
- When the condition clears, the event ends.
- If a trip ends while a condition is still active, `flush_vehicle()` closes the open event at the trip's completion timestamp.

Events are isolated per vehicle. Events from vehicle A are never mixed with events from vehicle B.

---

## 10. Behaviour Aggregation

`DriverBehaviourSummarizer.summarize()` rolls up all events for a completed trip into a `DriverBehaviourSummary`:

- Per-event-type counts and durations.
- Severity counts (minor, moderate, severe).
- `overall_severity` = the highest severity among all events, or `normal`.
- `maximum_speed_excess_kmh` — the peak speed over the limit during the trip.

---

## 11. Trip Persistence

### 11.1 Pre-creation

Before any telemetry is generated, `PersistenceService.create_trip()` writes a trip row with `status="in_progress"`. This ordering is required because `telemetry_samples` has a foreign key to `trips.trip_id`.

### 11.2 Completion

When a `VehicleRunner` completes its route, the runtime's `_persist_trip_completion` callback:

1. Computes `duration_seconds`, `distance_km`, `average_speed_kmh`, `maximum_speed_kmh`, `fuel_used_liters`, and `trip_score`.
2. Calls `persistence.complete_trip(...)` to update the trip row.
3. The same callback also pushes the completed trip into the WebSocket path via `TripSnapshotPublisher.publish()`.

### 11.3 Stale-Trip Recovery

At runtime startup, `persistence.abort_stale_trips()` marks every `in_progress` trip as `aborted`. This ensures that trips created by a previous (possibly crashed) runtime session are never reported as active. History and telemetry are preserved.

---

## 12. Trip Snapshot Contracts

### 12.1 Completed Trip (`TripBuilder.build()`)

`TripBuilder` is the single owner of final trip metrics. It builds a `TripSnapshot` from:

- `Trip` (distance, duration, status, timestamps)
- `AnalyticsContext` (vehicle/driver/route metadata)
- `DriverBehaviourSummary` (event counts, max speed excess)
- `RuntimeAnalyticsState` (fallback timestamp only)

The completed `TripSnapshot` includes `safety_score`, `grade`, and `completed_at`.

### 12.2 Active Trip (`build_active_trip_snapshot()`)

The active-trip builder builds a `TripSnapshot` for a trip that is still running. It sources:

- `runner.trip` — identity, route, started_at, live distance
- `AnalyticsContext` — vehicle/driver/route display metadata
- `RuntimeAnalyticsState` — live telemetry (current speed, fuel, ...)
- `DriverBehaviourAnalysis` — live point-in-time behaviour flags
- `AnalyticsSnapshot` — live behaviour flags via `snapshot_store`
- `AnalyticsEngine.get_accumulated_events()` — behaviour events so far this trip

Active-trip snapshots **never fabricate completion values**: `safety_score`, `grade`, and `completed_at` remain `None`/`False`/`0.0` where the value cannot yet be computed.

---

## 13. Trip Store

`TripStore` is an in-memory dictionary keyed by `trip_id`. It stores only **completed** trip snapshots. Active trips are never added to `TripStore`; they are broadcast directly via `TripSnapshotPublisher.publish_active()`.

Re-publishing the same `trip_id` (e.g. a retry) updates the stored snapshot rather than appending a duplicate.

---

## 14. WebSocket Trip Flow

```text
VehicleRunner completes route
    ↓
DriveVitalsRuntime._handle_trip_completions()
    ↓
  ├─ AnalyticsEngine.flush_vehicle()  →  all_events
  ├─ DriverStatisticsConsumer.record_trip()
  ├─ MaintenanceService.estimate_maintenance()
  ├─ AlertEngine.generate_alerts()
  └─ _trip_flush_callback
        ↓
  TripSnapshotPublisher.publish(summary, context, runtime_state, events, trip)
        ↓
  TripBuilder.build()  →  TripSnapshot
  TripStore.add(trip_snapshot)
  TripsSnapshot(trips=TripStore.all(), totals)
  trips_queue.put_nowait(trips_snapshot)
        ↓
  trips_worker → WebSocketManager.broadcast()
        ↓
  /ws/trips clients
```

Active-trip updates follow a parallel path:

```text
DriveVitalsRuntime._publish_active_trip_updates()
    ↓
  For each active runner:
    build_active_trip_snapshot(runner, now)
        ↓
  TripSnapshotPublisher.publish_active(snapshots, timestamp)
        ↓
  TripsSnapshot(trips=active_snapshots, totals)
  trips_queue.put_nowait(trips_snapshot)
        ↓
  /ws/trips clients
```

---

## 15. REST vs. WebSocket Trip Contracts

| Aspect | REST (`/api/v1/trips`) | WebSocket (`/ws/trips`) |
|--------|------------------------|------------------------|
| Data | Persisted completed + aborted trips | Active + completed trips (live) |
| Freshness | On-demand (polled) | Pushed every tick |
| Safety score | Always present (completed only) | `null` for active trips |
| Pagination | Yes (`limit`, `offset`) | No (full snapshot per broadcast) |
| Filtering | Yes (vehicle, driver, status, route_type) | No (client-side filter) |
| Merge behaviour | Source of truth for historical trips | Merged with REST in `LiveDataContext` |

The frontend merges both sources in `LiveDataContext.mergeTripsPayload()`: REST trips provide the historical baseline, and WebSocket snapshots overlay active trips and refresh completed trips with live data.

---

## 16. Key Invariants

1. **Active-trip ≤ vehicle-count invariant:** The number of active trips never exceeds the number of fleet assignments, because only `FleetRunner` can create active trips and it owns exactly one `VehicleRunner` per assignment.
2. **No fabricated completion metrics:** Distance, duration, and speed are derived from accumulated runtime state, not guessed.
3. **Trip rows before telemetry:** Trip rows are persisted before the first tick, satisfying the FK constraint.
4. **Stale-trip isolation:** `abort_stale_trips()` preserves all history and telemetry; only the status and an end timestamp are updated.
