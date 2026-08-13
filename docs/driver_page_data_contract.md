# Driver Page — Data Contract & Field Audit

> **Phase 0 deliverable.** Maps every visible Driver-page field to its source
> (REST / WebSocket / DB / derivation) and classifies each as
> `REAL` / `DERIVED` / `FABRICATED` / `BROKEN` / `MISSING`, then states the
> required implementation. This document is the ground truth for all later
> phases. **No application code was changed to produce this document.**

---

## 0. How to read this document

Classification legend:

| Tag | Meaning |
|---|---|
| `REAL` | Value traces to persisted DB data, REST, or a WebSocket payload with no invented fallback. |
| `DERIVED` | Deterministic calculation from `REAL` inputs. OK only if inputs are real and the formula is documented. |
| `FABRICATED` | Value invented in the frontend adapter/component to make the UI look populated. |
| `BROKEN` | Wire is present but the data never arrives or the wrong value is shown. |
| `MISSING` | No source exists end-to-end; currently rendered as `0` / empty / dead section. |
| `UNUSED` | Computed/persisted on the backend but never consumed by the Driver page. |

Status shorthand: `P0`–`P6` = implementation phase from the master prompt.

---

## 1. Data-flow overview

```
DB (PostgreSQL)                     Backend                              Frontend
──────────────                      ───────                              ────────
drivers          ──► GET /drivers ──────────────► listDrivers ──┐
driver_statistics─► GET /driver-statistics ─────► listDriverStatistics ─┤
trips            ──► GET /trips?driver_id= ─────► listTrips ────┤ LiveDataContext (hydrate: mount + reconnect)
vehicles         ──► GET /vehicles ─────────────► listVehicles ─┤
                                                              ▼
                                                adaptDrivers(drivers, driverStatistics, dashboard.vehicles)
                                                                     │
WS "dashboard" ──► DashboardBuilder.update() ──► VehicleDashboardSummary (per tick)
WS "trips"     ──► TripSnapshot on completion ──► merged by mergeTripsPayload
```

Trip completion path (backend):

```
tick ─► AnalyticsEngine.flush_vehicle ─► DriverStatisticsConsumer.record_trip
       ─► IntelligenceState.update_driver_statistics
       ─► persistence.persist_driver_statistics ─► DB driver_statistics        (runtime.py:1060-1074)
       ─► persistence.complete_trip ─► DB trips (distance/duration/fuel/score) (runtime.py:876-887)
```

**Key architectural fact:** every value the Driver page needs for history already
flows through `trips` (DB columns `distance_km`, `duration_seconds`,
`fuel_used_liters`, `average_speed_kmh`, `maximum_speed_kmh`, `trip_score`) and
through the trip-completion hook that already has the domain `Trip`
(`distance_travelled_km`, `fuel_used_liters`, `started_at`, `completed_at`) in
hand at `runtime.py:1060-1067`. The frontend only needs: (1) those trip values
aggregated into persisted `driver_statistics`, and (2) a per-driver trips fetch.

---

## 2. Canonical safety model (definition before implementation)

Three incompatible score implementations exist today:

| # | Implementation | Where | Semantics |
|---|---|---|---|
| (a) | `DashboardBuilder._compute_driver_safety(active_events)` | `backend/dashboard/services/dashboard_builder.py:451-465` | Momentary deduction from **currently active** events; clean moment ⇒ 100. **This is LIVE EVENT STATE, not driver safety.** |
| (b) | `compute_safety_score(...)` (density, exponential) | `backend/analytics/driver_statistics/safety.py:29-64` | Persisted driver-level score from completed-trip event density. **This is the canonical DRIVER SAFETY SCORE.** |
| (c) | `_compute_safety_score` → `compute_safety_score_for_summary` | `runtime.py:176-183`, `safety.py:67-85` | Per-completed-**trip** score (persisted as `trips.trip_score`, surfaced as grade + `TripSnapshot.safety_score`). **This is the TRIP SAFETY SCORE.** |

Model that must be adopted:

- **LIVE EVENT STATE** — what is happening right now (active event flags/types, speed, braking). Displayed separately, never merged into the historical score.
- **DRIVER SAFETY SCORE** — canonical, persisted `driver_statistics.safety_score` (b). Shown on card, drawer, ranking, overview. One definition, one source.
- **TRIP SAFETY SCORE** — `trips.trip_score` (c) per completed trip.
- **CURRENT RISK STATE** — `LOW / MEDIUM / HIGH / CRITICAL` classification computed from the canonical driver score (+ optionally current live condition), explicitly documented in one place.

Frontend adapter must **stop merging (a) into (b)** (currently `live?.driver_safety_score ?? stats?.safety_score ?? 100`).

---

## 3. Field-by-field contract

### 3.1 Driver object produced by `frontend/src/services/driverAdapter.js`

Source abbreviations: `REST drivers` = `GET /drivers`; `REST stats` = `GET /driver-statistics`; `WS dash` = WebSocket `dashboard_snapshot` → `VehicleDashboardSummary`; `WS trips` = WebSocket trips snapshot.

| Field | UI location | Source | Transformation | Status | Required implementation |
|---|---|---|---|---|---|
| `id`, `name`, `initials` | Card header, drawer header, ranking | `REST drivers` (`driver_id`, `first_name`, `last_name`) | `getInitials()` | `REAL` | none |
| `status` | Card status badge, drawer header | `WS dash` `operational_status` | `mapStatus()` | `REAL` — **except** `TRIP COMPLETED` falls through to `offline` | `P6` add `TRIP COMPLETED` mapping |
| `vehicleId`, `vehicleName` | Card, drawer | `WS dash` `vehicle_id`, `vehicle_name` | passthrough | `REAL` | none |
| `speed`, `rpm`, `throttle`, `brake`, `fuelLevel`, `engineLoad`, `coolantTemp` | Card (speed/RPM), drawer live telemetry grid | `WS dash` | `?? 0` when absent | `REAL` (live) — `0` fallback renders as value, not "no data" | `P6` render `—`/`No data` instead of `0` when absent |
| `healthScore` | **Drawer headline ring** (`smoothHealth`) | `WS dash` `overall_health_score` | passthrough | `REAL` but **WRONG SOURCE**: this is VEHICLE health | `P0` drawer ring must use canonical driver safety score |
| `safetyScore` | Card ring, ranking, overview avg | `live?.driver_safety_score ?? stats?.safety_score ?? 100` | fallback chain | `DERIVED` when stats exist; **`FABRICATED` `100` fallback**; mixes momentary (a) with persisted (b) | `P0` use only persisted `safety_score`; no `?? 100`; empty state when absent |
| `riskLevel` | Card/drawer risk badge, overview count | `riskFor(score, stats?.aggression_score)` | thresholds <60/<75/<85 | `DERIVED` — but input is the polluted score | `P0` recompute from canonical score only |
| `behaviourState` / `trend` | Drawer trend label | hardcoded `'declining'/'stable'` + session `computeTrend` cache | — | `FABRICATED` / `BROKEN` (resets to stable on reload; no history) | `P1+` derive from persisted history; `P0` stop showing trend when no history |
| `activeEventTypes` | Card indicators, drawer Active Events | `WS dash` `active_event_types` | passthrough | `REAL` (live) | none |
| `lastActive` | Card/drawer relative time | `WS dash` `last_updated_at` | `useRelativeTime` | `REAL` | none |
| `totalDistanceKm` | Drawer Metrics | `REST stats` `total_distance_km` | passthrough | `REAL` | none |
| `tripsCompleted` | Drawer Metrics, ranking subtitle | `REST stats` `total_trips` | passthrough | `REAL` | none |
| `averageSpeedKmh` | Drawer Metrics | `stats.total_driving_time_seconds` (DB column) | `distance / (seconds/3600)` | **`MISSING`** — column never written ⇒ always `0` | `P1` engine aggregates duration; `P2` repo persists; schema already exposes |
| `fuelEfficiencyKmPerL` | Drawer Metrics | `stats.fuel_efficiency` (DB column) | passthrough | **`MISSING`** — column never written ⇒ always `0` | `P1/P2` engine computes `distance / fuel`, repo persists |
| `drivingHours` | Drawer Metrics | `stats.total_driving_time_seconds` | `/ 3600` | **`MISSING`** — always `0` | `P1/P2` as above |
| `tripsToday` | Card footer, drawer overview | **hardcoded `0`** (`driverAdapter.js:107`) | — | **`FABRICATED`** | `P2` derive from `GET /trips?driver_id=&status=completed` filtered to today (via `TripRead.completed_at`) |
| `performanceHistory` | Drawer Performance Trend | **hardcoded `[]`** (`driverAdapter.js:108`) | — | **`FABRICATED`** | `P2+` build from completed-trip scores (`trips.trip_score` ordered by `completed_at`) or history table |
| `scoreBreakdown` | Drawer Score Breakdown | `buildScoreBreakdown()` | `efficiency = score + 5`; braking/accel/speed = score minus live-event constants | **`FABRICATED`** | `P0` remove; `P4` rebuild from real per-behaviour event densities + persisted `efficiency_score` |
| `behaviourDistribution` | Drawer Behaviour Distribution | `buildBehaviourDistribution()` | `smoothDriving = 100 − events×5`; `idle: 0` | **`FABRICATED`** | `P0` remove; show real event counts/rates only |
| `behaviour.*` (count/trend/severity/active) | Card indicators, drawer Behaviour Analysis | `REST stats` event counts + `WS dash` flags | `behaviourBlock()` | `count` `REAL` for speeding/harsh/aggressive; **`FABRICATED` `count:1` when live-active & count 0** (`driverAdapter.js:13`); `trend` hardcoded `'stable'`; `high_rpm_events` via residual | `P0` remove count fabrication + hardcoded trends; `P1` persist real `high_rpm` |

### 3.2 Page-level components

| Component / section | Field | Source | Status | Required implementation |
|---|---|---|---|---|
| `DriverOverview` — Total Drivers | `drivers.length` | `REST drivers` | `REAL` | none |
| `DriverOverview` — Average Safety Score | mean of `safetyScore` | inherits 3.1 `safetyScore` | `DERIVED`, contaminated by `100` fallback | `P0` compute from canonical scores; empty state when no stats |
| `DriverOverview` — High Risk Drivers | count riskLevel high/critical | inherits `riskLevel` | `DERIVED` | `P0` as above |
| `DriverOverview` — Active Drivers Now | count `status==='active'` | `WS dash` | `REAL` | none |
| `DriverCard` — telemetry (speed/RPM) | — | `WS dash` | `REAL` | `P6` no-data styling |
| `DriverCard` — indicators list | `smoothDriving` "✓" row | `liveBehaviours.length === 0` | `DERIVED` (live-only); duplicated `✓` glyph | `P6` fix glyph duplication (`DriverCard.jsx:225`) |
| `DriverCard` / `DriverProfileDrawer` — "No trips today" | `tripsToday` | hardcoded | `FABRICATED` | `P2` real value; show "No data" if not fetchable |
| `DriverProfileDrawer` — Live Telemetry grid | 8 items | `WS dash` | `REAL` | `P6` health item relabeled as vehicle health |
| `DriverProfileDrawer` — Active Events | event list | `WS dash` `active_event_types` | `REAL` (live) | none; must be visually separated from historical (`P6`) |
| `DriverProfileDrawer` — Performance Trend | `useDriverPerformance(driver.id)` | returns `null` (`useDrivers.js:46-48`) | **`BROKEN`** — section never renders | `P4` wire to real history; empty state "Not enough completed trips" |
| `DriverRanking` — trend icon/color | `getDriverTrend(driver.score)` | magnitude only (`utils/trend.js:15-23`) | **`FABRICATED`** | `P4` real delta from history; `P6` handle fleets < 6 without overlapping sections |
| `DriversPage` — empty state | inline "No drivers match" | filter result | `REAL` but conflates "no data" with "no match" | `P6` Skeleton/EmptyState/OfflineBanner per Vehicle Health |

### 3.3 `driver_statistics` table — column-by-column truth

DB model: `backend/db/models/driver_statistics.py`. Schema: `backend/api/v1/schemas/driver_statistics.py`. Writer: `persistence_service.persist_driver_statistics` → `DriverStatisticsRepository.upsert`.

| Column | Written today? | Source of write | Status | Required implementation |
|---|---|---|---|---|
| `total_trips` | ✅ | `statistics.total_trips` | `REAL` | none |
| `total_distance_km` | ✅ | `statistics.total_distance` | `REAL` | none |
| `safety_score` | ✅ | `DriverScoreCalculator` (density) | `REAL` | canonical for UI (`P0`) |
| `aggression_score` | ✅ | calculator | `REAL` | none (used in risk) |
| `efficiency_score` | ✅ | calculator | `REAL` | `P4` use in breakdown instead of `score+5` |
| `speeding_events` | ✅ | `overspeed_count` | `REAL` | none |
| `harsh_braking_events` | ✅ | `harsh_braking_count` | `REAL` | none |
| `aggressive_throttle_events` | ✅ | `harsh_acceleration_count` | `REAL` | none |
| `high_rpm_events` | ⚠️ residual | `total − harsh − overspeed − accel` (`persistence_service.py:273-279`) | `DERIVED` (fragile; engine-computed count discarded) | `P1` add `high_rpm_count` to domain model, pass through directly |
| `total_driving_time_seconds` | ❌ | — | **`MISSING`** (default 0) | `P1` engine sums trip durations; `P2` repo param + write |
| `average_trip_score` | ❌ | — | **`MISSING`** (default 0) | `P1` engine averages `trip_score`; `P2` write |
| `fuel_efficiency` | ❌ | — | **`MISSING`** (default 0) | `P1` engine `total_distance / total_fuel`; `P2` write |

### 3.4 Engine / domain gaps — `backend/analytics/driver_statistics/`

| Item | Status | Detail |
|---|---|---|
| `DriverStatisticsEngine.compute_statistics` | ✅ aggregates | trips, distance, all 4 event counts (incl. `high_rpm_count` internally, `_EventCounters`) |
| `DriverStatisticsEngine` | ❌ | does **not** aggregate duration, fuel, or average trip score |
| Domain model `models/driver_statistics.py` | ❌ | omits `high_rpm_count`, duration, fuel, avg trip score — so `high_rpm_count` is dropped at the boundary even though it is counted |
| `Trip` (domain, `fleet/models/trip.py`) | ✅ | already carries `distance_travelled_km`, `fuel_used_liters`, `maximum_speed_kmh`, `started_at`, `completed_at` — the engine receives this object in `record_trip` |

### 3.5 Backend API inventory

| Endpoint | Exists? | Notes |
|---|---|---|
| `GET /api/v1/drivers`, `GET /api/v1/drivers/{id}` | ✅ `REAL` | `api/v1/routers/drivers.py` |
| `GET /api/v1/driver-statistics`, `GET /api/v1/driver-statistics/{id}` | ✅ `REAL` | `api/v1/routers/driver_statistics.py`; schema already exposes the 3 missing columns |
| `GET /api/v1/trips?driver_id=&status=completed` | ✅ `REAL` | `api/v1/routers/trips.py:36-39`, `trip_service.py:55-56`; returns rich `TripRead` (score, grade, event counts, route) |
| `GET /api/v1/trips/{id}` | ✅ `REAL` | same router; reusable for `TripDrawer` |
| `GET /driver-summary/{driver_id}` | ❌ `MISSING` | frontend `endpoints.js:41` declares `summary.driver` but backend has no router (`api/v1/__init__.py`); `IntelligenceState.get_all_driver_statistics()` exists but is never exposed |

Decision for `P3` (per master prompt §9): implement `GET /driver-summary/{driver_id}` **only if** it is the cleanest contract. Alternative: frontend composes the existing three endpoints (`driver-statistics/{id}` + `trips?driver_id=` + WS live) — no new backend endpoint needed. Recommend: add `/driver-summary` as a thin aggregate only after P1/P2 land real columns; until then compose from existing endpoints.

---

## 4. Summary: REAL vs FABRICATED vs MISSING

**REAL (keep as-is):** identity, status, live telemetry, active events, persisted event counts (3 types), total trips, total distance, safety/aggression/efficiency scores, trip history data (`trips` + `TripRead`/`TripSnapshot`), trips filtering, persistence pipeline.

**FABRICATED (remove in P0):**
1. `tripsToday: 0` — `driverAdapter.js:107`
2. `performanceHistory: []` — `driverAdapter.js:108`
3. `?? 100` safety fallback — `driverAdapter.js:69`
4. `efficiency = score + 5` — `driverAdapter.js:36`
5. score-breakdown subtractions from live booleans — `driverAdapter.js:33-35`
6. `smoothDriving = 100 − events×5`, `idle: 0` — `driverAdapter.js:60-63`
7. `count: 1` fabrication — `driverAdapter.js:13`
8. hardcoded `trend: 'stable'` — `driverAdapter.js:16`
9. magnitude-based `getDriverTrend` — `utils/trend.js:15-23`

**BROKEN (fix):** `useDriverPerformance()` returns `null` (`useDrivers.js:46-48`); drawer ring shows vehicle health (`DriverProfileDrawer.jsx:285`); `TRIP COMPLETED` status maps to offline; stale stats after trip completion (no refresh in `LiveDataContext`); ranking small-fleet overlap.

**MISSING (build in P1–P5):** `total_driving_time_seconds`, `average_trip_score`, `fuel_efficiency`, canonical `high_rpm_events`, trips-today, performance history/trend, benchmarking, deterministic insights, loading/offline/empty states.

---

## 5. Implementation map (phase → files)

| Phase | Change | Files |
|---|---|---|
| **P0** Remove fabrication | adapter emits only real values; empty states; canonical score on card+drawer | `frontend/src/services/driverAdapter.js`, `components/drivers/DriverProfileDrawer.jsx`, `components/drivers/DriverCard.jsx`, `components/drivers/DriverRanking.jsx`, `utils/trend.js`, `hooks/useDrivers.js` |
| **P1** Engine truth | aggregate duration/fuel/avg-trip-score; carry `high_rpm_count` through domain model | `backend/analytics/driver_statistics/driver_statistics_engine.py`, `models/driver_statistics.py`, `persistence_service.py` (pass-through) |
| **P2** Persistence | repo writes the 3 missing columns + canonical high_rpm; migration if `server_default` change needed | `backend/db/repositories/driver_statistics_repository.py`; `db/migrations/versions/` new revision if needed; frontend refresh after trip completion (`LiveDataContext.jsx` + trips WS signal) |
| **P3** API contracts | `/driver-summary` (or compose existing); register router; tests | `api/v1/routers/`, `api/v1/__init__.py`, `tests/api/` |
| **P4** Trips + trends | per-driver trip history in drawer (reuse `TripRead`/`mapTrips`/`TripDrawer`), real PerformanceTrend, real ranking deltas, benchmarking | `frontend/src/components/drivers/*`, `utils/trips.js`, `hooks/useDrivers.js`, `services/api/tripApi.js` |
| **P5** Insights | deterministic rule-based insights from persisted data | backend aggregate or frontend pure functions on real data |
| **P6** UI quality | Skeleton/Empty/Offline/No-data states, live-vs-historical separation, glyph fixes, `TRIP COMPLETED` status, small-fleet ranking | `frontend/src/pages/Drivers.jsx`, `components/drivers/*`, `services/driverAdapter.js` |

Reference patterns to mirror: `frontend/src/pages/VehicleHealth.jsx`, `hooks/useVehicleHealthFilters.js`, `components/trips/TripDrawer.jsx`, `utils/trips.js`, `hooks/useTripsFilters.js`.

---

## 6. Sources inspected

- Frontend: `services/driverAdapter.js`, `hooks/useDrivers.js`, `utils/trend.js`, `components/drivers/{DriverCard,DriverProfileDrawer,DriverMetrics,DriverBehaviourTimeline,DriverRanking,DriverOverview}.jsx`, `pages/Drivers.jsx`, `context/LiveDataContext.jsx`, `api/endpoints.js`, `services/api/{driverApi,tripApi}.js`, `utils/trips.js`, `hooks/useTripsFilters.js`.
- Backend: `dashboard/services/dashboard_builder.py`, `dashboard/schemas/dashboard_payload.py`, `application/runtime.py`, `application/intelligence_state.py`, `application/consumers/driver_statistics_consumer.py`, `analytics/driver_statistics/{driver_statistics_engine,models/driver_statistics,aggregators/driver_score_calculator,safety,config}.py`, `analytics/behaviour/aggregation/summary.py`, `db/models/{driver_statistics,trip}.py`, `db/repositories/driver_statistics_repository.py`, `db/persistence_service.py`, `api/v1/{routers/trips.py,services/trip_service.py,services/driver_statistics_service.py,schemas/{driver_statistics,trip}.py,__init__.py}`, `fleet/models/trip.py`, `trips/schemas/trip_payload.py`, `db/migrations/versions/`.
- Tests: `tests/api/test_driver_statistics.py`, `tests/integration/test_intelligence_persistence.py`.
