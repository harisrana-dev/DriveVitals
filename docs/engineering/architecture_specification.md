# DriveVitals — Complete Architecture Specification

> Written from a full read of the repository (backend, frontend, docs, research, scripts, deployment).
> This document specifies the architecture as it exists today. Where code diverges from
> `docs/Project_Bible` / design docs, the divergence is flagged explicitly.

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Repository Layout](#2-repository-layout)
3. [Module-by-Module Specification](#3-module-by-module-specification)
4. [The 20 Architecture Questions](#4-the-20-architecture-questions)
5. [Documented-vs-Implemented Deltas](#5-documented-vs-implemented-deltas)
6. [Recreating the Architecture](#6-recreating-the-architecture)

---

## 1. System Overview

DriveVitals is a **Python 3.13 backend** (FastAPI + asyncio) plus a **React 18 + Vite frontend**,
simulating a fleet of vehicles (a "digital twin" of a physical fleet) that emits one telemetry
sample per vehicle per second. The backend runs a single event loop with several concurrent
asyncio tasks:

- the **fleet runtime** (per-vehicle simulation, `tick_seconds = 1.0`),
- a **telemetry pipeline** (fan-out of every sample to registered consumers),
- an **analytics engine** (per-sample, in-memory behaviour analysis + state),
- **streaming snapshot builders + publishers** (dashboard snapshot, trip snapshot),
- **WebSocket workers** (broadcast snapshots to connected browsers),
- **persistence** (async writes of trips/telemetry/alerts to PostgreSQL).

Two end-user surfaces consume the live stream:

- the **Dashboard** (fleet overview, live per-vehicle telemetry cards, vehicle health),
- the **Trips** page (completed trip summaries as they finish).

Product identity (per `docs/design/DriveVitals_analytics_product_BP.md`): an **AI-powered Fleet
Intelligence Platform** — an interpretation layer between vehicles and operators, **not** a bare
OBD-II dashboard. The simulation mode exists only until real OBD-II (ELM327) hardware is adopted
(`docs/design/DigitalTwinArchitecture/04_vehicle_simulation_mode.md`).

### Runtime picture (as started by `backend/api/main.py`)

```
main.py (FastAPI lifespan)
 ├─ runtime_task        → DriveVitalsRuntime.run()  [fleet tick loop]
 ├─ snapshot_worker_task→ reads snapshot_queue → WebSocketManager.broadcast
 └─ trips_worker_task   → reads trips_queue     → WebSocketManager.broadcast
```

---

## 2. Repository Layout

| Path | Responsibility |
|---|---|
| `backend/` | Python package (FastAPI service + engine + pipeline + fleet + analytics) |
| `backend/maintenance/` | Maintenance recommendation subsystem (completed milestone) |
| `backend/alerts/` | Alert model + generators + engine (generators stubbed) |
| `backend/fleet/` | Vehicle simulation runtime, telemetry generator, factory, models |
| `backend/analytics/` | Streaming analytics: behaviour, context, vehicle health, etc. |
| `backend/pipeline/` | Telemetry fan-out pipeline |
| `backend/application/` | Application wiring / `DriveVitalsRuntime` orchestrator |
| `backend/api/` | FastAPI app, REST + WebSocket endpoints, streaming publishers |
| `backend/db/` | SQLAlchemy models, session, repositories, migrations |
| `backend/persistence/` | **Dormant/legacy** persistence layer (0-byte `database.py`, empty dirs) |
| `backend/state/` | **Orphaned legacy** state manager (imports non-existent modules) |
| `backend/telemetry/` | Canonical `TelemetrySample` + legacy `TelemetryPacket` chain |
| `backend/shared/` | Shared base classes (mostly empty placeholders) |
| `frontend/` | React 18 + Vite 5 single-page application |
| `docs/` | Project Bible, engineering, design, team docs |
| `research/` | OBD-II / driver-behaviour research notes |
| `ml/` | Dataset builder (placeholder ML pipeline) |
| `scripts/` | Run/demo/smoke scripts |
| `tests/` | pytest suite |
| `deployment/` | docker-compose |
| `docker-compose.yml`, `requirements.txt`, `README.md` | Root infrastructure files |

---

## 3. Module-by-Module Specification

Each entry: **Purpose · Responsibilities · Inputs · Outputs · Dependencies · Internal flow ·
External flow**.

---

### 3.1 `backend/application/runtime.py` — `DriveVitalsRuntime`

- **Purpose**: The central orchestrator. Owns the lifetime of every subsystem and starts the
  telemetry-producing loop.
- **Responsibilities**: construct and hold instances of the analytics engine, fleet runner,
  dashboard builder, trip store/builder, publishers; expose `run()` (start + run) and `stop()`.
- **Inputs**: configuration/persistence objects supplied via constructor injection.
- **Outputs**: none directly; drives all downstream consumers via the telemetry sink.
- **Dependencies**: `PersistenceService`, `AnalyticsEngine`, `FleetRunner`,
  `DashboardBuilder`, `DashboardSnapshotPublisher`, `TripSnapshotPublisher`, trip
  store/builder, analytics snapshot stream/subscribers.
- **Internal flow**: constructed with a `PersistenceService`; wires every consumer into the
  telemetry pipeline; `run()` enters the fleet tick loop (blocking asyncio task started from
  FastAPI lifespan).
- **External flow**: FastAPI lifespan calls `run()`/`stop()`.

---

### 3.2 `backend/pipeline/telemetry_pipeline.py` — `TelemetryPipeline`

- **Purpose**: fan-out point for every telemetry sample to every interested consumer.
- **Responsibilities**: define the `TelemetryConsumer` Protocol (consumers expose
  `consume(sample)` or equivalent); register/unregister consumers; publish samples.
- **Inputs**: `TelemetrySample`.
- **Outputs**: forwards the same sample to each registered consumer.
- **Dependencies**: `TelemetrySample`, consumer protocol.
- **Internal flow**: `register(consumer)` adds to a set; `publish(sample)` iterates the set and
  calls `consumer.consume(sample)` (the docstring documents fan-out to the Analytics Engine,
  a Persistence Consumer, and a WebSocket Consumer).
- **External flow**: called by the fleet runtime sink per sample per vehicle per tick.

---

### 3.3 `backend/analytics/engine/analytics_engine.py` — `AnalyticsEngine`

- **Purpose**: the primary telemetry consumer; turns raw telemetry into per-driver behaviour
  state and per-vehicle snapshots.
- **Responsibilities**: consume samples; maintain runtime state per vehicle; run driver
  behaviour analysis; maintain the analytics snapshot (vehicle state + fleet summary) and emit it
  to subscribed stream handlers.
- **Inputs**: `TelemetrySample`.
- **Outputs**: `AnalyticsSnapshot` (to snapshot stream subscribers); derived state.
- **Dependencies**: context/state stores, behaviour analyser, snapshot stream +
  `AnalyticsSnapshotStream` subscribers.
- **Internal flow** (documented in its module docstring):
  `Telemetry → Runtime State → Analysis Input → Driver Behaviour Analysis → Behaviour Events
  → Trip-Level Behaviour Summary`.
- **External flow**: consumes from pipeline; snapshot stream subscribers push into dashboard /
  trip publishers.

---

### 3.4 `backend/fleet/runtime/fleet_runner.py` — `FleetRunner`

- **Purpose**: timekeeper + dispatcher for the simulated fleet.
- **Responsibilities**: own a set of `VehicleRunner`s; `tick()`/`tick_all()` advance each vehicle
  one simulation step (`tick_seconds = 1.0`); forward each produced `TelemetrySample` to a
  caller-provided sink (constructor-injected `TelemetrySink` callable).
- **Inputs**: `VehicleRunner` instances (via `add_assignment`), tick clock.
- **Outputs**: `TelemetrySample` per vehicle per tick.
- **Dependencies**: `VehicleRunner`, `TelemetrySink` callable. **No** direct analytics / DB /
  WebSocket coupling.
- **Internal flow**: `add_assignment(vehicle_runner)`; `tick_all()` → for each runner →
  `runner.tick()` → sample → `sink(sample)`.
- **External flow**: runtime loop calls `tick_all()`.

---

### 3.5 `backend/fleet/runtime/vehicle_runner.py` — `VehicleRunner`

- **Purpose**: one simulated vehicle.
- **Responsibilities**: model the vehicle's physics/state machine; progress a trip; emit one
  `TelemetrySample` per `tick()`.
- **Inputs**: `Vehicle`, `Driver`, `Route` (assignment), a generator of raw telemetry values.
- **Outputs**: `TelemetrySample`.
- **Dependencies**: `TelemetrySample`, telemetry generator, route/vehicle/driver models.
- **Internal flow** (documented in module): `tick()` advances position along the route, speed
  derived from route speed limits, randomized within physics constraints (seeded for
  determinism), fuel/engine metrics computed; completes trip when distance is exhausted.
- **External flow**: called once per second by `FleetRunner.tick_all()`.

---

### 3.6 `backend/fleet/config/fleet_factory.py` — `FleetFactory`

- **Purpose**: deterministic fixture generation for the simulated fleet.
- **Responsibilities**: build 6 `Vehicle`, 6 `Driver`, 6 `Route`, 6 `DriverAssignment`
  (assignment pairs each driver to a vehicle/route).
- **Inputs**: none (module-level data/constants).
- **Outputs**: model instances.
- **Dependencies**: fleet models.
- **External flow**: consumed by `DriveVitalsRuntime` / API startup.

---

### 3.7 `backend/fleet/models/` — fleet domain models

- **Purpose**: pure data models for the simulated world.
- **Members**: `Vehicle`, `Driver`, `Route`, `DriverAssignment`, `Trip` (plus `models/__init__.py`).
- **Responsibilities**: carry fields (vehicle id/metadata, driver id/name, route waypoints/speed
  limits, assignment linking, trip lifecycle state).
- **Dependencies**: none significant (dataclasses / simple classes).
- **External flow**: produced by `FleetFactory`, consumed by simulation + persistence.

---

### 3.8 `backend/telemetry/models/telemetry_sample.py` — `TelemetrySample`

- **Purpose**: the **canonical** telemetry schema (frozen `dataclass`).
- **Responsibilities**: define one sample: vehicle id, timestamp, speed, rpm, throttle,
  coolant temp, intake temp, fuel level/consumption, engine load, GPS, etc.
- **Outputs**: used by pipeline, analytics, persistence, alerts, maintenance, dashboard.
- **Dependencies**: none (pure dataclass).
- **External flow**: produced by `VehicleRunner`, consumed everywhere downstream.

---

### 3.9 `backend/telemetry/models.py` — `TelemetryPacket` (legacy)

- **Purpose**: legacy pydantic telemetry packet.
- **Responsibilities**: retained only for the dead chain
  `TelemetryDispatcher → TelemetryValidator → TelemetryProcessor`.
- **Status**: **orphaned** — nothing instantiates the dispatcher/validator/processor chain; all
  live code paths use `TelemetrySample`.

---

### 3.10 `backend/analytics/` — analytics subsystem

Covered per-module (only modules containing real code are listed; the rest are 0-byte
placeholders — see §5):

- `engine/analytics_engine.py` — see §3.3.
- `behaviour/driver_behaviour_analyzer.py` — **DriverBehaviourAnalyzer**: stateless,
  converts a `TelemetrySample` into a `DriverBehaviourAnalysis` (frozen dataclass of behaviour
  flags/scores). **DriverBehaviourAnalysis**: the canonical behaviour snapshot.
- `behaviour/behaviour_event_tracker.py` — **BehaviourEventTracker**: accumulates per-trip
  behaviour events (instances of risky behaviour) as samples stream in.
- `behaviour/driver_behaviour_summarizer.py` — **DriverBehaviourSummarizer**: computes a
  summary from accumulated events/behaviour (drives the trip-level behaviour summary step).
- `context/analytics_context.py` — **AnalyticsContext**: the mutable runtime analysis context
  (one per vehicle) holding accumulated state.
- `context/analytics_context_store.py` — **AnalyticsContextStore**: keyed store of contexts.
- `state/runtime_state.py` — **RuntimeState**: live per-vehicle operational state
  (speed/rpm/odometer/last sample time, in-trip flag, etc.).
- `state/runtime_state_store.py` — **RuntimeStateStore**: keyed store of runtime states.
- `input/analysis_input.py` — **AnalysisInput**: normalized input envelope fed to analysers.
- `streaming/snapshot_stream.py` — **AnalyticsSnapshotStream**: pub/sub sink; subscribers
  register via `subscribe(...)`; snapshots are dispatched to each subscriber.
- `vehicle_health/` — completed subsystem (see §3.11).
- `driver_statistics_engine.py`, `aggregators/driver_score_calculator.py` —
  `NotImplementedError` stubs.
- `behaviour/driver_score.py`, `behaviour/driver_trends.py`, `rules/`, `trip/`, `vehicle/`,
  `fleet/`, `models/` — 0-byte placeholders.

- **Inputs**: `TelemetrySample` (via `AnalyticsEngine`).
- **Outputs**: `AnalyticsSnapshot` (fleet summary + per-vehicle state/behaviour/health);
  behaviour events; trip-level summaries.
- **Dependencies**: shared dataclasses, stores, stream.
- **Internal flow**:
  ```
  AnalyticsEngine.consume(sample)
   → RuntimeStateStore.update(vehicle_id, sample)
   → AnalyticsContextStore.get(vehicle_id)
   → AnalysisInput(sample, context)
   → DriverBehaviourAnalyzer.analyse(input) → DriverBehaviourAnalysis
   → BehaviourEventTracker.record(...)   → events
   → snapshot stream → subscribers
  ```
- **External flow**: snapshot stream subscribers include the dashboard snapshot publisher;
  trip events feed the trip publisher.

---

### 3.11 `backend/analytics/vehicle_health/` — Vehicle Health subsystem (completed)

- **Purpose**: per-vehicle health scoring from a rolling telemetry window.
- **Responsibilities**: maintain per-vehicle deques (`window_size = 20`); run 5 analyzers;
  produce a weighted overall health status; support per-vehicle flush.
- **Members**: `VehicleHealthEngine` (public facade),
  `HealthConfig`/`DEFAULT_HEALTH_CONFIG` (thresholds per component), `HealthStatus` enum
  (`healthy`, `warning`, `critical`, etc.), 5 component analyzers
  (engine, transmission, brakes, tyres, electrical — each a `Strategy`), per-analyzer
  thresholds.
- **Inputs**: `TelemetrySample` stream; `HealthConfig`.
- **Outputs**: `VehicleHealthSnapshot` (per-component + overall status, weights, config).
- **Dependencies**: telemetry schema; health config; dataclasses.
- **Internal flow**: on each sample → update rolling window → each analyzer scores its component
  against thresholds → weighted overall = 0.30·engine + 0.20·transmission + 0.20·brakes +
  0.15·tyres + 0.15·electrical → status thresholds (`90`/`70` band) → snapshot.
- **External flow**: consumed by `MaintenanceService`, alert generators (stub), dashboard
  health cards, frontend `useVehicleHealth` hook.

---

### 3.12 `backend/maintenance/` — Maintenance subsystem (completed)

- **Purpose**: project-based maintenance recommendations per vehicle.
- **Responsibilities**: compute interval-based recommendations (odometer-mod-interval), derive
  priority/severity, estimate cost + due date, expose a single service facade.
- **Members**:
  - `models/maintenance_type.py` — `MaintenanceType` enum (14 types: oil_change, brake_pads,
    brake_fluid, air_filter, cabin_filter, fuel_filter, spark_plugs, coolant_flush,
    transmission_fluid, battery_check, tyres_rotation, timing_belt, wipers, general_inspection).
  - `models/maintenance_recommendation.py` — redesigned `MaintenanceRecommendation`
    (maintenance_type, priority, severity, remaining_km, reason, recommended_action,
    estimated_cost, estimated_due_date).
  - `models/maintenance_record.py` — `MaintenanceRecord`, persists type (shares
    `MaintenanceType`), status, cost, performed_at.
  - `maintenance_config.py` — `PriorityThresholds` (5000 / 2000 / 500 km bands),
    `SeverityThresholds` (90 / 70), `EngineOperatingThresholds` (overheat 105 °C,
    redline 6200 rpm, stress factor 0.75), `ServiceProfile` (interval + cost per type),
    14 profiles, `daily_distance_km = 100`.
  - `estimation/rules.py` — pure functions: `health_factor`, `interval_remaining_km
    (interval − odometer mod interval)`, `priority_for`, `severity_for`,
    `estimated_due_date`, `PRIORITY_RANK`.
  - `estimators/maintenance_estimator.py` — interface: `estimate(*, health_snapshot,
    odometer_km, telemetry_sample=None) → list[MaintenanceRecommendation]`.
  - `estimators/component_estimator.py` — shared base; emit rule: emit when `remaining ≤ LOW
    band` **or** `score < 90` → emit a full recommendation plan.
  - `estimators/` — 5 thin estimators (engine, transmission, brakes, tyres, electrical).
  - `maintenance_service.py` — `MaintenanceService.estimate_maintenance(...)`: dedupe +
    merge all estimators, sort by `(PRIORITY_RANK, remaining_km, component, type)`;
    `build_records(...)`: deterministic IDs `vehicle:type:projected_odometer`.
- **Inputs**: `VehicleHealthSnapshot`, `odometer_km`, optional `TelemetrySample`.
- **Outputs**: sorted recommendations / maintenance records.
- **Dependencies**: vehicle health snapshot model; its own config/models.
- **Internal flow**: for each estimator → compute remaining km & score-based trigger → build
  recommendation → merge → sort → return; records path converts recommendations to records.
- **External flow**: called by alert generator (stub) and dashboard/frontend `useMaintenance`.

---

### 3.13 `backend/alerts/` — alert subsystem

- **Purpose**: unified alert model + generation framework (engine and generators currently
  stubbed).
- **Members**: `models/fleet_alert.py` — frozen `FleetAlert` (alert_id, vehicle_id, alert_type,
  severity, message, created_at, optional driver_id/trip_id); `AlertType`
  (maintenance/telemetry/health/trip); `AlertSeverity`
  (critical/high/medium/low/info). `generators/` — `AlertContext`, `AlertGenerator` base +
  `HealthAlertsGenerator` (raised `NotImplementedError` — rules TODO),
  `MaintenanceAlertsGenerator`, `TelemetryAlertsGenerator`, `TripAlertsGenerator`.
  `engine/alert_engine.py` — `AlertEngine` whose `generate_alerts(...)` raises
  `NotImplementedError`.
- **Inputs (design)**: `AlertContext` (health snapshot, maintenance recommendations,
  telemetry, trip summaries).
- **Outputs (design)**: `FleetAlert` instances.
- **Dependencies**: health + maintenance models.
- **External flow (design)**: alerts → persistence; later → dashboard APIs / frontend `/alerts`.
- **Status**: skeleton only; generation logic not yet implemented.

---

### 3.14 `backend/api/` — HTTP + WebSocket layer

- `main.py` — FastAPI app; module-level singletons:
  - `runtime = DriveVitalsRuntime(persistence_service=PersistenceService())`
  - `snapshot_queue: asyncio.Queue[DashboardSnapshot]`
  - `snapshot_publisher = DashboardSnapshotPublisher(queue=snapshot_queue, builder=runtime.dashboard_builder)`
  - `trip_store = TripStore()`, `trip_builder = TripBuilder()`
  - `trip_publisher = TripSnapshotPublisher(queue=trips_queue, builder=trip_builder, store=trip_store)`
  - lifespan starts `runtime_task`, `snapshot_worker_task`, `trips_worker_task`.
- `routes.py` — REST + legacy `/ws/dashboard` WebSocket route (uses `websocket_manager`
  singleton).
- `dependencies.py` — `websocket_manager = WebSocketManager()` singleton.
- `websocket/dashboard.py` — `snapshot_queue`; `snapshot_worker()` pops snapshots, serializes
  (`asdict` + isoformat timestamps, per-vehicle `last_updated_at`), broadcasts
  `{"type": "dashboard_snapshot", "data": ...}`; `/ws/dashboard` endpoint accepts connections
  and loops `receive_text` (heartbeat ping).
- `websocket/trips.py` — `trips_queue`; `trips_worker()` broadcasts
  `{"type": "trips_snapshot", "data": ...}`; `/ws/trips` endpoint.
- `websocket/manager.py` — `WebSocketManager` with `connect`/`disconnect`/`broadcast`/
  `connection_count`.
- `websocket/snapshot_publisher.py` — `DashboardSnapshotPublisher.publish(snapshot)` →
  `builder.update(snapshot)` → `queue.put_nowait(snapshot)`.
- `websocket/trip_publisher.py` — `TripSnapshotPublisher.publish(summary, context,
  runtime_state, events)` → `trip_builder.build(...)` → `trip_store.add(trip)` → aggregate
  totals (total_trips, total_distance, avg_safety_score, total_fuel) → `TripsSnapshot` →
  `trips_queue`.
- `services/` (in repo research) — `trip_builder.py`, `trip_store.py`, `trip_payload.py`,
  `dashboard_builder.py`, `dashboard_payload.py`, `state/` (legacy orphan).

---

### 3.15 `backend/db/` — SQLAlchemy persistence (real)

- **Purpose**: the **active** database layer (2.x, async).
- **Members**: `base.py` — `Base(DeclarativeBase)`; `session.py` — async session factory;
  `models/` — ~12 models (Vehicle, Driver, Route, DriverAssignment, Trip, TelemetryRecord,
  HealthSnapshot/Record, MaintenanceRecord, Alert, etc.), all with `TimestampMixin`
  (`created_at`/`updated_at`, tz-aware, client + server defaults); `repositories/` —
  async repository classes; `persistence_service.py` — `PersistenceService` (writes trips,
  telemetry, alerts asynchronously via `asyncio.ensure_future`, honoring FK ordering: trip rows
  before telemetry rows, etc.); `migrations/` — Alembic migration environment (Alembic 1.18.5).
- **Inputs**: in-memory snapshots/models from the runtime.
- **Outputs**: PostgreSQL rows.
- **Dependencies**: SQLAlchemy 2.0.51, asyncpg 0.31.0.
- **External flow**: `postgres:16` container (`docker-compose.yml`).

---

### 3.16 `backend/persistence/` — dormant legacy layer

- **Purpose/status**: legacy; `database.py` is 0 bytes; `migrations/`, `models/`,
  `repositories/` directories are empty. **Not wired into any live code path.** Real layer is
  `backend/db/`.

---

### 3.17 `backend/state/` — orphaned legacy module

- **Status**: orphaned. `state_manager.py` imports non-existent
  `dashboard.connection_manager` and `analytics.event_metadata`, and uses non-package-relative
  imports. Nothing in the current `backend.*` package imports it. Scheduled for removal or
  restoration.

---

### 3.18 `backend/telemetry/` (generator side)

- `obd_generator.py` — simulates raw OBD-II style reads feeding the `VehicleRunner` physics
  (stands in for ELM327 hardware until real adoption).
- `models/telemetry_sample.py` — canonical sample (§3.8).
- `models.py` — legacy `TelemetryPacket` (§3.9).

---

### 3.19 `backend/shared/` — shared base layer

- **Status**: placeholders. `enums.py`, `exceptions.py` are 0 bytes. `base/` contains base
  classes used across subsystems (e.g. component base classes). Not a common "utils" hub yet.

---

### 3.20 `frontend/` — React SPA

- **Stack**: React 18, Vite 5, react-router-dom ^7.18.1, recharts ^3.10.1, lucide-react.
  No Redux/Zustand, no axios/react-query, no socket.io/WS lib, no CSS framework (inline styles
  + CSS variables).
- **Entry/config**: `main.jsx` (ReactDOM.createRoot), `App.jsx` (router), `vite.config.js`
  (no proxy — direct `ws://localhost:8000`).
- **Routing**:
  | Route | Source of data |
  |---|---|
  | `/` | `GetStarted` / Introductionpage (static) |
  | `/login`, `/signup` | client-side validation only; login navigates to `/dashboard` |
  | `/dashboard` | live via `useDashboardSocket` |
  | `/fleet` | live via `useDashboardSocket` |
  | `/trips` | live via `useTripsSocket` |
  | `/drivers` | derived from live dashboard snapshot (`useDrivers` + driverAdapter) |
  | `/alerts` | derived from live dashboard snapshot (`useAlerts`) |
  | `/live-telemetry` | static placeholder |
  | `/analytics` | static placeholder |
- **Contexts**: `DashboardContext`, `FleetContext`, `TripsContext`, `ThemeContext`,
  `TripDrawerContext`, `VehicleDrawerContext`.
- **Hooks**: `useDashboardSocket`, `useTripsSocket`, `useFleetData`, `useAlerts`,
  `useDrivers`, `useMaintenance`, `useTripsData`, `useVehicleHealth`, `useTripsFilters`,
  `useFleetFilters`, `useRelativeTime`, `useSmoothValue`, `useTheme`.
- **Services**: `websocket.js` (native WebSocket client; dispatches on message `type`:
  `"dashboard_snapshot"`, `"trips_snapshot"`), `driverService.js`, `driverAdapter.js`.
- **Utils**: `alerts.js`, `health.js`, `maintenance.js`, `trend.js`.
- **External flow**: opens `ws://localhost:8000/ws/dashboard` and `/ws/trips`; renders live
  snapshots; derives alerts/drivers client-side from the dashboard snapshot.

---

### 3.21 `ml/`, `research/`, `scripts/`, `deployment/`, `tests/`

- `ml/dataset_builder.py` — builds a dataset from recorded telemetry (placeholder for future
  predictive ML; see `docs/design/analytics_engine/future_ml_integration.md`).
- `research/notes/*.md` — `fleet_telematics`, `Driver_behaviour_notes`, `obd2-based-ML`.
- `scripts/` — `run_backend.py` (uvisorn/run app), `run_fleet_demo.py`,
  `run_fleet_telemetry.py`, `simulate_vehicle.py`, `test_obd_connection.py`,
  `test_dashboard_websocket.py`, `reset_database.py`.
- `deployment/docker-compose.yml` + root `docker-compose.yml` — `postgres:16`.
- `tests/` — pytest suite (52 passing; 10 pre-existing failures isolated to
  `test_analytics_engine.py`).

---

## 4. The 20 Architecture Questions

### 1. What is the overall architecture style?

An **event-driven, streaming pipeline architecture** wrapped in **layered, orchestrated
monolithic backend** with a **thin REST + WebSocket facade** and a **decoupled React SPA**.
The core is a single-process asyncio runtime where telemetry flows through a publish/subscribe
pipeline (producer → pipeline → analytics → snapshot stream → publishers → WebSocket →
browser). Components are connected by **observer/publish–subscribe** and **constructor
injection** rather than hard dependencies. It is monolithic (one deployable, one event loop),
event-sourced-in-memory (live state kept in RAM; only events/trips/alerts are persisted).

### 2. What are the major subsystems?

1. Fleet Simulation Runtime (`backend/fleet/`) — vehicles, drivers, routes, assignments, tick loop.
2. Telemetry Pipeline (`backend/pipeline/`) — fan-out of samples.
3. Streaming Analytics Engine (`backend/analytics/`) — behaviour, state, snapshots, vehicle health.
4. Vehicle Health subsystem (`backend/analytics/vehicle_health/`) — rolling health scores.
5. Maintenance subsystem (`backend/maintenance/`) — interval/priority/cost recommendations.
6. Alert subsystem (`backend/alerts/`) — unified alert model + generation framework (stubbed).
7. Streaming/WebSocket layer (`backend/api/websocket/`) — queues, workers, publishers, manager.
8. HTTP/REST layer (`backend/api/`) — FastAPI app + routes.
9. Persistence layer (`backend/db/`) — async SQLAlchemy + Alembic + PersistenceService.
10. Application orchestrator (`backend/application/runtime.py`) — `DriveVitalsRuntime`.
11. Frontend SPA (`frontend/`) — dashboard, fleet, trips, drivers, alerts views.
12. Docs/Research/ML tooling (`docs/`, `research/`, `ml/`, `scripts/`, `tests/`).

### 3. What are the backend layers?

- **Presentation**: `backend/api/` — FastAPI routes + WebSocket endpoints + streaming publishers.
- **Application/Orchestration**: `backend/application/runtime.py` — composition root.
- **Domain**: `backend/fleet/models/`, `backend/analytics/`, `backend/alerts/`,
  `backend/maintenance/`, `backend/telemetry/models/` — simulation, analysis, health, maintenance,
  alerts.
- **Infrastructure/Persistence**: `backend/db/` (SQLAlchemy + Alembic + repositories +
  PersistenceService).
- **Cross-cutting**: `backend/pipeline/` (transport), `backend/shared/` (base classes; mostly
  placeholders), `backend/config.py` (empty; no centralized config module yet).

### 4. What are the frontend layers?

- **Views/Pages**: `pages/*` (GetStarted, Login, Signup, Dashboard, Fleet, Trips, Drivers,
  Alerts, LiveTelemetry, Analytics).
- **Context/State**: `context/*` (Dashboard, Fleet, Trips, Theme, TripDrawer, VehicleDrawer).
- **Hooks (logic)**: `hooks/*` (socket hooks, data hooks, filters, theme, time formatting).
- **Services (I/O)**: `services/*` (native WebSocket client, fleet/driver services).
- **Utilities**: `utils/*` (alert/health/maintenance/trend derivations).
- **Assets/components**: `assets`, `components` (presentational components).

### 5. What is the complete data flow?

```
FleetRunner.tick_all()                       [per second]
  → VehicleRunner.tick() → TelemetrySample
  → TelemetryPipeline.publish(sample)        [fan-out]
      → AnalyticsEngine.consume(sample)
          → RuntimeStateStore, AnalyticsContextStore, DriverBehaviourAnalyzer
          → AnalyticsSnapshotStream → subscribers
      → (future) persistence consumer, (future) WebSocket consumer
  → AnalyticsSnapshotStream.subscribers
      → DashboardSnapshotPublisher.publish(snapshot)
          → DashboardBuilder.update(snapshot)
          → snapshot_queue
          → snapshot_worker → WebSocketManager.broadcast
              → {"type": "dashboard_snapshot", "data": {...}}
              → browsers (Dashboard/Fleet pages)
      → TripSnapshotPublisher.publish(summary, context, runtime_state, events)
          → TripBuilder.build → TripStore.add → TripsSnapshot (totals)
          → trips_queue → trips_worker → WebSocketManager.broadcast
              → {"type": "trips_snapshot", "data": {...}}
              → browsers (Trips page)
  → Trip completion → PersistenceService (async, FK-ordered)
```

### 6. What is the complete telemetry lifecycle?

1. **Produce**: `VehicleRunner.tick()` computes physics from route/speed/random-seed and emits a
   `TelemetrySample` (frozen dataclass).
2. **Publish**: `TelemetryPipeline.publish(sample)`.
3. **Consume (analytics)**: `AnalyticsEngine` updates runtime state + behaviour context; pushes
   an `AnalyticsSnapshot` to the snapshot stream.
4. **Derive (health)**: vehicle-health engine folds the sample into the rolling window and
   recomputes component + overall health.
5. **Derive (maintenance, on demand)**: maintenance service uses the health snapshot + odometer.
6. **Stream (dashboard)**: snapshot publisher → queue → WebSocket → browser.
7. **Persist (as needed)**: trips/telemetry rows written async to PostgreSQL.

### 7. What is the complete runtime lifecycle?

1. `main.py` imports module-level singletons (runtime, publishers, stores, queues).
2. FastAPI `lifespan` starts three asyncio tasks: `runtime_task`, `snapshot_worker_task`,
   `trips_worker_task`.
3. `DriveVitalsRuntime.run()` wires all consumers into the telemetry pipeline and enters the
   fleet tick loop (blocking; ~1 Hz × 6 vehicles).
4. Per tick: `FleetRunner.tick_all()` → samples → pipeline → analytics → snapshot stream →
   publishers → queues.
5. Snapshot/trip workers serialize and broadcast to connected WebSocket clients.
6. On shutdown: lifespan cancels tasks; runtime `stop()`; sessions/DB cleaned up.

### 8. What is the complete analytics pipeline?

```
TelemetrySample
  → [Runtime State]      RuntimeStateStore.update(vehicle_id, sample)
  → [Analysis Input]     AnalysisInput(sample, context)
  → [Driver Behaviour]   DriverBehaviourAnalyzer.analyse(input)
  → [Behaviour Events]   BehaviourEventTracker.record(...)
  → [Trip Summary]       DriverBehaviourSummarizer / trip-level aggregation
  → [Snapshot]           AnalyticsSnapshot (vehicle state + fleet summary)
  → [Stream]             AnalyticsSnapshotStream → subscribers
```

(Per the `AnalyticsEngine` docstring: Telemetry → Runtime State → Analysis Input → Driver
Behaviour Analysis → Behaviour Events → Trip-Level Behaviour Summary.)

### 9. What is the complete WebSocket communication?

- **Channels**: `/ws/dashboard` (dashboard snapshots) and `/ws/trips` (trip snapshots). A legacy
  duplicate `/ws/dashboard` route exists in `routes.py` using the same `websocket_manager`.
- **Producer side**: publishers `put_nowait` into `asyncio.Queue`s; dedicated worker tasks pop
  and broadcast.
- **Manager**: single `WebSocketManager` singleton tracks connected sockets
  (`connect`/`disconnect`/`connection_count`) and broadcasts a dict.
- **Wire protocol**: JSON envelope `{"type": "dashboard_snapshot"|"trips_snapshot", "data": ...}`
  where `data` is `asdict` with ISO-formatted timestamps (per-vehicle `last_updated_at`).
- **Client side**: native `WebSocket` in `services/websocket.js`; message `type` dispatches to
  the matching context hook. Heartbeat via `receive_text` ping on the dashboard socket.

### 10. What is the complete database interaction?

- **Stack**: SQLAlchemy 2.0.51 async ORM, asyncpg driver, Alembic migrations, PostgreSQL 16
  (Docker).
- **Schema**: ~12 tables; every model inherits `Base(DeclarativeBase)` +
  `TimestampMixin` (`created_at`, `updated_at` — tz-aware, client + server defaults).
- **Write path**: in-memory models (e.g. completed trips) → `PersistenceService` →
  `asyncio.ensure_future(...)` async writes; FK ordering respected (trips before telemetry, etc.).
- **Read path**: currently minimal; repositories exist for future REST reads.
- **Layer**: `backend/db/` (active) vs `backend/persistence/` (dormant legacy, 0-byte files).

### 11. What is the complete simulation interaction?

- `FleetFactory` builds 6 vehicles/6 drivers/6 routes/6 assignments.
- `FleetRunner` holds a `VehicleRunner` per assignment; `tick_all()` advances each once per
  second.
- `VehicleRunner.tick()`: advances distance; speed follows route speed limits with seeded
  random noise; derives rpm/load/fuel/coolant metrics from physics formulas; ends a trip when the
  route distance is exhausted; emits one `TelemetrySample`.
- Simulation samples are indistinguishable from real samples for every downstream consumer
  (analytics, health, maintenance, dashboard), enabling a clean swap to OBD-II later.

### 12. How will future real OBD-II integration work?

- The simulation is the **only** producer today; the pipeline consumer API is
  schema-based (`TelemetrySample`), so a real `OBDTelemetrySource` implementing the same sink
  contract can replace `VehicleRunner` without touching consumers.
- Hardware groundwork exists in `docs/engineering/elm327.md`, `obd2.md`, `pid_decoding.md`,
  `vehicle_telemetry.md`, `bitmap_in_obd.md`; `scripts/test_obd_connection.py` tests an ELM327
  device; `backend/telemetry/obd_generator.py` currently simulates OBD-style reads.
- Future work: swap in ELM327 reads → `TelemetrySample`; retire `TelemetryPacket` legacy chain;
  wire persistence of continuous telemetry; then enable predictive ML
  (`ml/dataset_builder.py`, `docs/design/analytics_engine/future_ml_integration.md`).

### 13. What is the complete API request lifecycle?

- **Lifespan**: import singletons → start runtime + worker tasks → serve.
- **REST** (FastAPI): request → route handler (`routes.py`) → services/repositories → JSON.
- **WebSocket**: client connects → `WebSocketManager.connect` → server loops
  (`receive_text` for heartbeat) → server pushes serialized snapshots via `broadcast` → client
  disconnects → `WebSocketManager.disconnect`.
- No REST read endpoints for dashboard data today; the dashboard is pushed over WebSocket.

### 14. What are the component relationships?

- `DriveVitalsRuntime` **owns** `PersistenceService`, `AnalyticsEngine`, `FleetRunner`,
  `DashboardBuilder`, `TripStore`/`TripBuilder`, publishers, stream subscribers.
- `FleetRunner` → (sink) `TelemetryPipeline`.
- `TelemetryPipeline` → `AnalyticsEngine` (consumer).
- `AnalyticsEngine` → context/state stores, behaviour analysers → `AnalyticsSnapshotStream`.
- `AnalyticsSnapshotStream` → `DashboardSnapshotPublisher`, `TripSnapshotPublisher`.
- `DashboardSnapshotPublisher` → `DashboardBuilder` → `snapshot_queue`.
- `TripSnapshotPublisher` → `TripBuilder` + `TripStore` → `trips_queue`.
- Workers → `WebSocketManager` → browsers.
- `maintenance` ↔ `vehicle_health` (health snapshot → maintenance recommendations).
- `alerts` (design) ← health + maintenance + telemetry + trips; → persistence.

### 15. Which components act as central orchestrators?

1. `DriveVitalsRuntime` — composition root + lifecycle (runtime.py).
2. `FleetRunner` — simulation timekeeper.
3. `TelemetryPipeline` — sample fan-out hub.
4. `AnalyticsEngine` — analytics hub (state + behaviour + snapshot emission).
5. `AnalyticsSnapshotStream` — pub/sub hub for snapshots.
6. `WebSocketManager` — broadcast hub.
7. `MaintenanceService` — recommendation orchestration (merges estimators, sorts).
8. `VehicleHealthEngine` — per-vehicle health orchestration (window + analyzers).
9. `PersistenceService` — async persistence orchestration.

### 16. Which components are service-only (no orchestration role)?

- `DriverBehaviourAnalyzer`, `BehaviourEventTracker`, `DriverBehaviourSummarizer`
  (pure analysis services).
- `DashboardBuilder`, `DashboardSnapshot` serializer, `TripBuilder`, `TripStore`,
  `TripSnapshot` aggregate builders.
- Component health analyzers (`EngineAnalyzer`, `TransmissionAnalyzer`, …).
- Maintenance estimators (`EngineEstimator`, `BrakeEstimator`, …) and `estimation/rules.py`
  (pure functions).
- Repositories and SQLAlchemy model mappers.

### 17. Which components communicate directly (bypassing the orchestrator)?

- `VehicleRunner → TelemetrySample` → `TelemetryPipeline` (direct sink call per tick).
- `FleetFactory → VehicleRunner/Vehicle/Driver/Route/Assignment` (direct construction).
- `AnalyticsEngine → RuntimeStateStore/AnalyticsContextStore/DriverBehaviourAnalyzer` (direct
  calls within the engine's `consume`).
- `AnalyticsSnapshotStream → subscribers` (direct dispatch to each registered subscriber).
- `snapshot_worker → WebSocketManager.broadcast` (direct broadcast).
- `maintenance estimators → MaintenanceService` (direct estimation calls merged by the service).
- `vehicle health engine → component analyzers` (direct per-component scoring).

### 18. Which components never communicate (by design)?

- **Frontend ↔ Database**: no direct DB access; UI only talks WebSocket/REST.
- **FleetRunner ↔ AnalyticsEngine/DB/WebSocket**: the runner only forwards samples to its sink;
  it has no knowledge of downstream consumers.
- **DashboardBuilder ↔ TripStore**: snapshot and trip flows are separate queues/workers.
- **Legacy `backend/state/` ↔ everything**: orphaned; nothing imports it.
- **`TelemetryPacket` chain ↔ live pipeline**: legacy dispatcher/validator/processor never
  instantiated by live code.
- **`backend/persistence/` ↔ `backend/db/`**: dormant legacy layer not wired to the active layer.

### 19. What is the folder hierarchy?

See the repository table in §2 (each folder's responsibility + state, including placeholders).

### 20. What architecture patterns are used?

1. **Pipeline pattern** — `TelemetryPipeline` fan-out; `AnalyticsEngine` chain (state →
   input → behaviour → events → summary); `estimate → merge → sort → build_records`.
2. **Observer / Publish–Subscribe** — `AnalyticsSnapshotStream` + subscribers; queue/worker
   streaming; `WebSocketManager` broadcast.
3. **Strategy pattern** — component health analyzers; maintenance estimators; alert generators
   (`AlertGenerator` base); telemetry generators.
4. **Service Layer** — `MaintenanceService`, `VehicleHealthEngine`, `PersistenceService`,
   `AnalyticsEngine`, `WebSocketManager`.
5. **Repository pattern** — `backend/db/repositories/`.
6. **Dependency Injection (constructor)** — `DriveVitalsRuntime(persistence_service=...)`,
   publishers injected with queues/builders/stores; fleet runner injected with sink.
7. **Singleton (module-level)** — `WebSocketManager`, `runtime`, publishers, queues in `main.py`.
8. **Value objects / frozen models** — `TelemetrySample`, `FleetAlert`, `DriverBehaviourAnalysis`,
   `MaintenanceRecommendation` (frozen dataclasses; deterministic IDs).
9. **Factory** — `FleetFactory`, maintenance record builder.
10. **Template method** — shared `ComponentEstimator`/`AlertGenerator` base with override points.
11. **Concurrency via asyncio** — one event loop; tasks for runtime, snapshot worker, trips
    worker; queues for decoupling producers/consumers.

---

## 5. Documented-vs-Implemented Deltas

- `backend/shared/enums.py`, `backend/shared/exceptions.py`, `backend/config.py`,
  `backend/persistence/database.py` — **0 bytes**.
- `backend/persistence/` — dormant legacy; real layer is `backend/db/`.
- `backend/state/` — orphaned; imports non-existent `dashboard.connection_manager`,
  `analytics.event_metadata`; nothing imports it.
- `backend/telemetry/models.py` (`TelemetryPacket` + dispatcher/validator/processor chain) —
  legacy; unused by live code (canonical = `TelemetrySample`).
- `backend/analytics/rules/`, `trip/`, `vehicle/`, `fleet/`, `models/`,
  `behaviour/driver_score.py`, `behaviour/driver_trends.py`,
  `dashboard/models/*.py`, `dashboard/mapper.py` — **empty placeholders**.
- `driver_statistics_engine.py`, `aggregators/driver_score_calculator.py`,
  `AlertEngine.generate_alerts`, all four alert generators — `NotImplementedError` stubs.
- `docs/Project_Bible` describes an OBD-II telematics platform (early final-year-project framing)
  while the implemented product is a simulated fleet-intelligence platform; Digital Twin docs
  describe the forward vision. Treat Project Bible + design docs as **vision**, this spec as
  **as-built**.

---

## 6. Recreating the Architecture

1. **Runtime bootstrap**: `DriveVitalsRuntime` with a `PersistenceService`; `main.py`
  lifespan starts runtime + two worker tasks.
2. **Simulation**: `FleetFactory` → 6 assignments → `FleetRunner(tick_seconds=1.0)` →
  `VehicleRunner.tick()` emits `TelemetrySample`s to a sink = `TelemetryPipeline.publish`.
3. **Analytics**: `AnalyticsEngine.consume` keeps `RuntimeStateStore`/`AnalyticsContextStore`,
  runs `DriverBehaviourAnalyzer`, pushes `AnalyticsSnapshot` through `AnalyticsSnapshotStream`.
4. **Health**: `VehicleHealthEngine` folds samples into 20-sample windows; 5 analyzers →
  weighted overall (0.30/0.20/0.20/0.15/0.15) → `HealthStatus`.
5. **Maintenance**: `MaintenanceService.estimate_maintenance(health_snapshot, odometer_km)`
  merges 5 estimators; rules: interval mod odometer, bands 5000/2000/500 km, severity 90/70,
  due-date from `daily_distance_km=100`, engine stress factor 0.75 / overheat 105 °C /
  redline 6200 rpm.
6. **Streaming**: `DashboardSnapshotPublisher` → `DashboardBuilder.update` → `snapshot_queue` →
  `snapshot_worker` → `WebSocketManager.broadcast`. Trips similarly via `trip_publisher` →
  `TripStore` → `trips_queue` → `trips_worker`.
7. **Frontend**: `services/websocket.js` opens `/ws/dashboard` + `/ws/trips`; contexts consume
  `{"type": ...}` envelopes; pages derive drivers/alerts from the dashboard snapshot.
8. **Persistence**: trips/telemetry/alerts → `PersistenceService` → async SQLAlchemy writes to
  PostgreSQL (Alembic migrations).
