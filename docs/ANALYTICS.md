# DriveVitals — Analytics Documentation

> **Source of truth:** `backend/analytics/engine/analytics_engine.py`, `backend/analytics/behaviour/`, `backend/analytics/vehicle_health/`, `backend/analytics/driver_statistics/`, `backend/maintenance/`, `backend/alerts/`.
> All analytics in DriveVitals are **deterministic and rule-based**. No machine learning is used today.

---

## 1. Analytics Pipeline Overview

```text
TelemetrySample
    ↓
RuntimeStateStore.update()          ← live per-vehicle state
AnalyticsContextStore.get()         ← immutable trip context
    ↓
AnalysisInput(runtime_state, context)
    ↓
DriverBehaviourAnalyzer.analyse()   ← point-in-time behaviour flags
    ↓
BehaviourEventTracker.process()     ← temporal events (start/end)
    ↓
AnalyticsSnapshot                   ← vehicle state + behaviour + events
    ↓
AnalyticsSnapshotStream.publish()
    ↓
    ├─ DashboardSnapshotPublisher → /ws/dashboard
    ├─ TripSnapshotPublisher      → /ws/trips
    └─ Persistence subscriber      → DB (behaviour events)
```

At trip completion, additional downstream consumers fire:

- `DriverStatisticsEngine` aggregates the trip into driver-level statistics.
- `MaintenanceService` estimates maintenance recommendations from the final health snapshot.
- `AlertEngine` generates alerts from health, maintenance, telemetry, and trip data.

---

## 2. Driver Behaviour Detection

### 2.1 Point-in-Time Analysis

`DriverBehaviourAnalyzer.analyse(input)` evaluates a single `TelemetrySample` against configurable thresholds:

| Behaviour | Condition |
|-----------|-----------|
| `speeding` | `speed_kmh > context.speed_limit_kmh + threshold` |
| `harsh_braking` | `brake_pressure > threshold` during deceleration |
| `aggressive_throttle` | `throttle_position_percent > threshold` with increasing speed |
| `high_rpm` | `rpm > threshold` |

The analyzer returns a `DriverBehaviourAnalysis` dataclass containing boolean flags and severity metadata.

### 2.2 Event Coalescing

`BehaviourEventTracker` converts point-in-time detections into temporal events:

- **Start:** When a flag transitions from `False` to `True`, a new event begins.
- **End:** When the flag transitions back to `False`, the event closes with its duration, distance, and peak intensity.
- **Flush at trip end:** If a trip completes while a condition is still active, `flush_vehicle()` closes the event at the completion timestamp.

Events are isolated per vehicle. `_completed_events` is a `dict[str, list[BehaviourEvent]]`, ensuring no cross-vehicle contamination.

### 2.3 Aggregation

`DriverBehaviourSummarizer.summarize()` rolls up all events for a trip into a `DriverBehaviourSummary`:

- Per-event-type counts and total durations.
- Severity counts: `minor`, `moderate`, `severe`.
- `overall_severity` = highest severity across all events, or `normal`.
- `maximum_speed_excess_kmh` = peak speed over the limit.

---

## 3. Safety Scoring

### 3.1 Canonical Formula

Safety scoring is the single, distance-normalized exponential decay function in `backend/analytics/driver_statistics/safety.py`:

```python
weighted_density = events_per_km(
    harsh_braking_count * 2.0 +
    aggressive_throttle_count * 1.5 +
    speeding_count * 3.0 +
    high_rpm_count * 1.0,
    distance_km,
)

score = 100.0 * exp(-weighted_density * 0.35)
score = clamp(round(score, 2), 0, 100)
```

**Why density, not count?** A trip with 5 harsh brakes over 10 km is worse than 5 harsh brakes over 500 km. Density normalization ensures the score reflects behaviour intensity relative to opportunity, not raw event volume.

### 3.2 Grade Mapping

| Score | Grade |
|-------|-------|
| ≥ 90 | A |
| ≥ 80 | B |
| ≥ 70 | C |
| ≥ 60 | D |
| < 60 | F |

### 3.3 Where Scoring Occurs

- **Trip-level:** `compute_safety_score_for_summary()` in `TripBuilder.build()` and `_persist_trip_completion()` in `runtime.py`.
- **Driver-level:** `DriverStatisticsEngine` aggregates completed-trip summaries into standing per-driver statistics (stubbed in current codebase).

---

## 4. Vehicle Health

### 4.1 Subsystem Analyzers

`VehicleHealthEngine` coordinates five independent analyzers:

| Subsystem | Analyzer | Weight |
|-----------|----------|--------|
| Engine | `EngineHealthAnalyzer` | 0.30 |
| Brakes | `BrakeHealthAnalyzer` | 0.20 |
| Cooling | `CoolingHealthAnalyzer` | 0.20 |
| Transmission | `TransmissionHealthAnalyzer` | 0.15 |
| Fuel System | `FuelSystemHealthAnalyzer` | 0.15 |

Each analyzer maintains a rolling window of the last 20 telemetry samples and scores its component against configurable thresholds.

### 4.2 Overall Health

```python
overall_score = (
    0.30 * engine +
    0.20 * brakes +
    0.20 * cooling +
    0.15 * transmission +
    0.15 * fuel_system
)
```

**Status thresholds:**

| Score | Status |
|-------|--------|
| ≥ 90 | healthy |
| ≥ 70 | warning |
| < 70 | critical |

### 4.3 Health-to-Maintenance

`MaintenanceService.estimate_maintenance()` consumes a `HealthSnapshot`, vehicle metadata, and the current odometer. Five `MaintenanceEstimator` subclasses (one per subsystem) produce `MaintenanceRecommendation` objects, which are deduplicated, merged, and sorted by priority.

---

## 5. Alert Engine

### 5.1 Architecture

`AlertEngine` orchestrates four alert generators:

| Generator | Trigger |
|-----------|---------|
| `HealthAlertsGenerator` | Health status transitions |
| `TelemetryAlertsGenerator` | Live telemetry thresholds |
| `MaintenanceAlertsGenerator` | Maintenance recommendations |
| `TripAlertsGenerator` | Trip completion events |

### 5.2 Deduplication

`DuplicateSuppressor` prevents the same alert from re-emerging within a configurable cooldown window. The runtime uses `active_alert_keys()` to evaluate which conditions are currently triggered **before** deduplication, so persistent conditions inside the cooldown window are not incorrectly resolved.

### 5.3 Resolution

`PersistenceService.resolve_cleared_alerts()` transitions open alerts to `resolved` when their condition is no longer active. Two categories are handled:

- **Health / Telemetry alerts:** Resolved per tick in `_PersistenceTelemetryConsumer`.
- **Trip / Maintenance alerts:** Resolved at trip completion in `_handle_trip_completions()`.

---

## 6. Driver Statistics

`DriverStatisticsEngine` aggregates completed-trip behaviour summaries into standing per-driver statistics:

- Total trips, total distance, total driving time.
- Average trip score.
- Event counts (speeding, harsh braking, aggressive throttle, high RPM).
- Safety, aggression, and efficiency scores.

Currently the aggregation and score-calculation paths are implemented but the final `DriverScoreCalculator` is a stub (`NotImplementedError`).

---

## 7. Fuel Efficiency

Fuel efficiency is not computed as a standalone `km/L` metric in the current analytics pipeline. Fuel data is tracked as:

- `fuel_consumed_liters` per trip (derived from fuel-level percentage drop against a 60 L tank).
- `average_fuel_rate_lph` = `fuel_consumed_liters / (duration_seconds / 3600)`.

Future fuel-efficiency scoring is planned but not implemented.

---

## 8. Key Invariants

1. **Events are per-vehicle.** `BehaviourEventTracker` and `_completed_events` are keyed by `vehicle_id`.
2. **Distance-normalized scoring.** Safety score uses `events_per_km`, not raw counts.
3. **No fabricated scores.** Active trips report `safety_score: null`; scores are only computed at completion.
4. **Health window is bounded.** Each analyzer maintains exactly 20 samples; older samples are discarded.
