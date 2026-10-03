# DriveVitals — Testing Documentation

> **Source of truth:** `tests/`, `pytest.ini`.
> This document describes the test suite as it exists today.

---

## 1. Test Organization

```text
tests/
├── unit/                       # Fast, isolated tests
│   ├── test_active_trip_snapshot.py
│   ├── test_analytics_context.py
│   ├── test_analytics_engine.py
│   ├── test_driver_statistics_engine.py
│   ├── test_health_reasons.py
│   ├── test_runtime_resilience.py
│   ├── test_runtime_stale_trip_abort.py
│   ├── test_runtime_state_store.py
│   ├── test_runtime_trip_completion.py
│   ├── test_safety_score_sources.py
│   ├── test_safety_scoring.py
│   ├── test_scenario_parameters.py
│   ├── test_trip_snapshot_contract.py
│   └── test_vehicle_runner_peak_speed.py
├── integration/                # Multi-component tests
│   ├── test_active_trip_invariant.py
│   ├── test_alert_concurrency.py
│   ├── test_alert_lifecycle.py
│   ├── test_fleet_runtime.py
│   ├── test_intelligence_consumers.py
│   ├── test_intelligence_persistence.py
│   ├── test_runtime_shutdown.py
│   ├── test_scenario_assignments.py
│   ├── test_simulation_controller.py
│   ├── test_stale_trip_abort_persistence.py
│   └── test_telemetry_brake_percent.py
└── api/                        # FastAPI endpoint tests
    ├── test_alerts.py
    ├── test_auth.py
    ├── test_authorization.py
    ├── test_authorization_perimeter.py
    ├── test_bootstrap_admin.py
    ├── test_digital_twin.py
    ├── test_drivers.py
    ├── test_driver_statistics.py
    ├── test_empty.py
    ├── test_lifespan_shutdown.py
    ├── test_maintenance.py
    ├── test_maintenance_reconciliation.py
    ├── test_routes.py
    ├── test_settings.py
    ├── test_settings_integration.py
    ├── test_system.py
    ├── test_telemetry.py
    ├── test_trips.py
    ├── test_trip_deletion.py
    ├── test_vehicles.py
    ├── test_vehicle_health.py
    └── test_websockets.py
```

Additionally, `tests/test_analytics_api.py` sits at the `tests/` root. Total: 48 backend test files, 525 passing tests. The frontend has 23 Vitest suites (265 passing tests) under `frontend/src/**/*.test.js(x)`.

---

## 2. Running Tests

```bash
pytest                      # backend: 525 tests
cd frontend && npm test     # frontend: 23 suites, 265 tests
```

Configuration (`pytest.ini`):

```ini
asyncio_mode = auto
testpaths = tests
```

Uses `pytest-asyncio` for async tests and `httpx` for async FastAPI test clients. The API layer needs a live PostgreSQL instance: set `POSTGRES_PASSWORD`, and point `POSTGRES_DB` at a dedicated database whose name ends in `_test` (the suite refuses to run otherwise, because it drops and recreates the schema).

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

- One test file per router, exercising `GET` and (for alerts, trips, maintenance, auth, digital twin, settings) the supported mutations.
- Tests use a live test database session via FastAPI's dependency injection.
- WebSocket tests verify connection lifecycle and message receipt, including session enforcement (unauthenticated upgrades are rejected).

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
- **API test isolation is destructive, not transactional.** Each API test drops and recreates the whole schema through the `ids` fixture and reseeds it, which guarantees isolation but makes the layer slower than a rollback-based design and requires a dedicated `*_test` database.
- **Frontend linting is not part of `npm test`.** ESLint runs as its own step (`npm run lint`, also executed in CI).

---

## 6. Adding a New Test

1. Place unit tests in `tests/unit/`, integration tests in `tests/integration/`, and API tests in `tests/api/`.
2. Follow the existing naming convention: `test_<module_or_feature>.py`.
3. For async tests, use `pytest.mark.asyncio` (or rely on `asyncio_mode = auto`).
4. For API tests, use the `client` fixture from `tests/api/conftest.py`.
