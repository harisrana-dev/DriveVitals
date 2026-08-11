# Analytics Engine Architecture

## 1. Overview

The DriveVitals Analytics Engine is a modular processing system responsible for transforming raw vehicle telemetry into actionable information for fleet managers. It operates as a synchronous pipeline inside `AnalyticsEngine.consume()`, with no external framework dependencies.

The architecture follows a pipeline-based design in which each telemetry sample passes through a fixed sequence of analytical steps. Every step is a pure function or a stateful service with a single responsibility.

This modular architecture provides the following advantages:

* Separation of concerns
* High maintainability
* Easy extensibility
* Independent module testing
* Interpretable, deterministic outputs

---

## 2. Core Components

The Analytics Engine consists of the following major components:

* **Runtime State Store** — mutable per-vehicle operational state (speed, RPM, odometer, last sample time, in-trip flag).
* **Analytics Context Store** — immutable per-trip context (route, speed limit, driver, vehicle metadata).
* **Driver Behaviour Analyzer** — evaluates a single sample against thresholds and produces point-in-time behaviour flags.
* **Behaviour Event Tracker** — converts point-in-time flags into temporal events (start/end with duration and distance).
* **Behaviour Event Summarizer** — rolls up all events for a trip into a `DriverBehaviourSummary`.
* **Analytics Snapshot** — the point-in-time output contract: vehicle state + behaviour + events.
* **Analytics Snapshot Stream** — synchronous pub/sub sink that dispatches snapshots to subscribers.

---

## 3. High-Level Architecture

```text
                  TelemetrySample
                          │
                          ▼
              RuntimeStateStore.update()
                          │
                          ▼
              AnalyticsContextStore.get()
                          │
                          ▼
                   AnalysisInput
                          │
                          ▼
            DriverBehaviourAnalyzer.analyse()
                          │
                          ▼
            BehaviourEventTracker.process()
                          │
                          ▼
              AnalyticsSnapshot
                          │
                          ▼
           AnalyticsSnapshotStream
                          │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
   DashboardPublisher  TripPublisher  PersistenceSubscriber
```

The architecture is intentionally flat (not layered into validation/preprocessing/rule-engine sub-steps as earlier design docs suggested). Each `TelemetrySample` is consumed in a single synchronous pass, producing one `AnalyticsSnapshot`.

---

## 4. Data Flow Detail

### 4.1 Runtime State

`RuntimeStateStore.update(sample)` updates the mutable state for the sample's vehicle:

- Current speed, RPM, throttle, brake, coolant, engine load, fuel level, odometer.
- In-trip flag.
- Last sample timestamp.

### 4.2 Analysis Input

`AnalysisInput(runtime_state, context)` combines mutable runtime state with immutable analytics context into a single normalized envelope for the analyzer.

### 4.3 Behaviour Analysis

`DriverBehaviourAnalyzer.analyse(input)` evaluates the sample against configurable thresholds:

- `speeding`: speed exceeds route speed limit.
- `harsh_braking`: brake pressure exceeds threshold during deceleration.
- `aggressive_throttle`: throttle exceeds threshold with rising speed.
- `high_rpm`: RPM exceeds threshold.

Returns a `DriverBehaviourAnalysis` dataclass with boolean flags and severity metadata.

### 4.4 Event Tracking

`BehaviourEventTracker.process(analysis, timestamp)` converts point-in-time detections into temporal `BehaviourEvent` objects:

- Starts events when conditions become true.
- Ends events when conditions clear.
- At trip completion, `flush_vehicle()` closes any still-open events.

Events are isolated per vehicle.

### 4.5 Snapshot Emission

`AnalyticsSnapshot` is constructed with:

- `vehicle_id`, `driver_id`, `trip_id`, `timestamp`
- `telemetry` (the original `TelemetrySample`)
- `behaviour` (latest `DriverBehaviourAnalysis`)
- `completed_events` (events closed this tick)
- `active_event_types` (currently open event types)

The snapshot is stored in `AnalyticsSnapshotStore` and published onto `AnalyticsSnapshotStream`.

---

## 5. Downstream Consumers

Subscribers to `AnalyticsSnapshotStream`:

| Subscriber | Purpose |
|------------|---------|
| `DashboardSnapshotPublisher` | Builds `DashboardSnapshot` → `snapshot_queue` → `/ws/dashboard` |
| `TripSnapshotPublisher` | Builds `TripSnapshot` / `TripsSnapshot` → `trips_queue` → `/ws/trips` |
| `_PersistenceSnapshotSubscriber` | Persists completed behaviour events to PostgreSQL |

---

## 6. Trip Completion Path

When a vehicle's trip ends, the runtime calls `AnalyticsEngine.flush_vehicle()`:

1. `BehaviourEventTracker.flush_vehicle()` closes any open events at the completion timestamp.
2. Previously completed events are combined with flushed events.
3. `DriverBehaviourSummarizer.summarize()` produces a `DriverBehaviourSummary` with counts, durations, severities, and max speed excess.
4. The summary is stored for later retrieval by the trip publisher.

---

## 7. Safety Scoring

Safety scoring is **not** part of `AnalyticsEngine`. It is computed downstream by `compute_safety_score_for_summary()` in `backend/analytics/driver_statistics/safety.py` using the completed `DriverBehaviourSummary` and the trip's final distance.

This separation ensures that the analytics engine produces neutral, source-level data, and scoring is applied only when a trip is complete and the distance is known.
