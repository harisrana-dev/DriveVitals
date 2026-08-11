# DriveVitals — Testing Documentation

> **Source of truth:** `tests/`, `pytest.ini`.
> This document describes the test suite as it exists today.

---

## 1. Test Organization

```text
tests/
├── unit/              # Fast, isolated tests
│   ├── test_analytics_context.py
│   ├── test_analytics_engine.py
│   ├── test_runtime_state_store.py
│   ├── test_runtime_trip_completion.py
│   ├── test_runtime_resilience.py
│   ├── test_runtime_stale_trip_abort.py
│   ├── test_safety_scoring.py
│   ├── test_trip_snapshot_contract.py
│   └── test_active_trip_snapshot.py
├── integration/       # Multi-component tests
│   ├── test_fleet_runtime.py
│   ├── test_intelligence_consumers.py
│   ├── test_intelligence_persistence.py
│   ├── test_stale_trip_abort_persistence.py
│   ├── test_telemetry_brake_percent.py
│   └── test_active_trip_invariant.py
└── api/               # FastAPI endpoint tests
    ├── test_vehicles.py
    ├── test_drivers.py
    ├── test_routes.py
    ├── test_trips.py
    ├── test_telemetry.py
    ├── test_vehicle_health.py
    ├── test_driver_statistics.py
    ├── test_maintenance.py
    ├── test_alerts.py
    ├── test_system.py
    ├── test_websockets.py
    └── test_empty.py
```

---

## 2. Running Tests

```bash
pytest
```

Configuration (`pytest.ini`):

```ini
asyncio_mode = auto
testpaths = tests
```

Uses `pytest-asyncio` for async tests and `httpx` for async FastAPI test clients.

---

## 3. What Each Layer Protects

### 3.1 Unit Tests (`tests/unit/`)

- **Analytics context / engine:** Verify that `AnalyticsEngine.consume()` produces correct snapshots, events, and stream publications.
- **Runtime state store:** Verify per-vehicle state updates and lookups.
- **Safety scoring:** Verify the exponential decay formula, clamping, and grade mapping.
- **Trip snapshot contract:** Verify that `TripBuilder` and `build_active_trip_snapshot()` produce the correct `TripSnapshot` for both completed and active trips.
- **Trip completion:** Verify that `DriveVitalsRuntime._handle_trip_completions()` correctly computes metrics and calls callbacks.
- **Runtime resilience:** Verify that a failing telemetry publish or trip completion does not crash the fleet loop.
- **Stale-trip abort:** Verify that `abort_stale_trips()` transitions stale `in_progress` trips to `aborted` without modifying history.

### 3.2 Integration Tests (`tests/integration/`)

- **Fleet runtime:** End-to-end tick loop with real `FleetRunner`, `VehicleRunner`, and `TelemetryPipeline`.
- **Intelligence consumers:** Verify that `VehicleHealthConsumer` and `DriverStatisticsConsumer` receive and process telemetry correctly.
- **Intelligence persistence:** Verify that completed-trip intelligence (behaviour events, driver statistics, maintenance records, alerts) is persisted to the database.
- **Stale-trip abort persistence:** Verify the database-side stale-trip recovery.
- **Telemetry brake percent:** Verify that `brake_pressure` (0–1) is correctly converted to `brake_percent` (0–100) on persistence.
- **Active-trip invariant:** Verify that the active-trip set never exceeds the vehicle count and that completed trips are removed from the active set.

### 3.3 API Tests (`tests/api/`)

- One test file per router, exercising `GET` and (for alerts) `POST` endpoints.
- Tests use a live/test database session via FastAPI's dependency injection.
- WebSocket tests verify connection lifecycle and message receipt.

---

## 4. Critical Regression Protections

| Invariant / Behavior | Test Location |
|----------------------|---------------|
| Active-trip count ≤ vehicle count | `test_active_trip_invariant.py` |
| Stale trips are aborted at startup | `test_runtime_stale_trip_abort.py`, `test_stale_trip_abort_persistence.py` |
| Telemetry `brake_pressure` → `brake_percent` conversion | `test_telemetry_brake_percent.py` |
| Safety score density normalization | `test_safety_scoring.py` |
| Trip snapshot contract (completed vs. active) | `test_trip_snapshot_contract.py`, `test_active_trip_snapshot.py` |
| Runtime loop survives consumer failures | `test_runtime_resilience.py` |
| Completed-trip persistence (events, stats, maintenance, alerts) | `test_intelligence_persistence.py` |
| REST endpoint response shapes | `tests/api/test_*.py` |
| WebSocket connection lifecycle | `tests/api/test_websockets.py` |

---

## 5. Known Limitations

- **No coverage reporting configured.** The suite does not enforce a minimum coverage threshold.
- **No CI workflow.** Tests must be run locally.
- **API tests use a shared test database session** rather than fully isolated fixtures per test. This is acceptable for current development but should be hardened before treating the suite as a production regression gate.
- **`test_empty.py`** exists but currently contains no tests.

---

## 6. Adding a New Test

1. Place unit tests in `tests/unit/`, integration tests in `tests/integration/`, and API tests in `tests/api/`.
2. Follow the existing naming convention: `test_<module_or_feature>.py`.
3. For async tests, use `pytest.mark.asyncio` (or rely on `asyncio_mode = auto`).
4. For API tests, use the `client` fixture from `tests/api/conftest.py`.
