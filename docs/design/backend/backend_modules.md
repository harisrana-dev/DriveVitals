# Backend Module Design

## DriveVitals Backend Module Specification

**Version:** 2.0
**Project:** DriveVitals – Intelligent Fleet Vehicle Telemetry & Analytics Platform
**Status:** Reflects the current implementation (post-M2, pre-M3).

---

## 1. Purpose

The DriveVitals backend follows a modular, layered architecture built using FastAPI and asyncio. Each module has a single responsibility, making the system scalable, maintainable, and easy to extend.

The backend is responsible for:

- Simulating fleet telemetry (physics-inspired OBD-II-style generator)
- Running the fleet runtime (tick-driven vehicle/driver/route advancement)
- Distributing telemetry via a fan-out pipeline
- Running analytics (driver behaviour, vehicle health, driver statistics)
- Estimating maintenance recommendations
- Generating and resolving alerts
- Persisting data to PostgreSQL
- Serving REST APIs
- Streaming live snapshots over WebSockets

---

## 2. Backend Directory Structure

```text
backend/
├── api/
│   ├── main.py                  # FastAPI app + lifespan
│   ├── dependencies.py          # Shared dependencies (WebSocketManager, services)
│   ├── v1/
│   │   ├── routers/             # 10 REST routers (vehicles, drivers, routes, trips, telemetry, health, stats, maintenance, alerts, system)
│   │   ├── services/            # Business logic for REST reads + alert mutations
│   │   ├── schemas/             # Pydantic response models
│   │   └── dependencies.py      # Router-specific DI
│   └── websocket/
│       ├── dashboard.py         # /ws/dashboard route + snapshot_worker
│       ├── trips.py             # /ws/trips route + trips_worker
│       ├── manager.py           # WebSocketManager (connect/disconnect/broadcast)
│       ├── snapshot_publisher.py # Bridges AnalyticsSnapshotStream → asyncio.Queue
│       └── trip_publisher.py    # Bridges trip completion/active updates → asyncio.Queue
├── application/
│   ├── runtime.py               # DriveVitalsRuntime — composition root + main loop
│   ├── intelligence_state.py    # Shared health/statistics state for consumers
│   └── consumers/
│       ├── vehicle_health_consumer.py
│       └── driver_statistics_consumer.py
├── fleet/
│   ├── config/
│   │   ├── fleet_config.py      # Fleet configuration dataclass
│   │   └── fleet_factory.py     # Deterministic 6-vehicle/6-driver/6-route fixture generation
│   ├── models/
│   │   ├── vehicle.py
│   │   ├── driver.py
│   │   ├── route.py
│   │   ├── trip.py              # Trip state machine (ASSIGNED → STARTED → IN_PROGRESS → COMPLETED/ABORTED)
│   │   └── assignment.py
│   └── runtime/
│       ├── fleet_runner.py      # Coordinates VehicleRunner instances; ticks all active vehicles
│       ├── vehicle_runner.py    # Single simulated vehicle; produces TelemetrySample per tick
│       └── runtime_state.py     # Per-vehicle mutable runtime state (speed, RPM, odometer, etc.)
├── pipeline/
│   └── telemetry_pipeline.py    # Fan-out dispatcher (TelemetryConsumer protocol)
├── telemetry/
│   ├── models/
│   │   └── telemetry_sample.py  # Canonical TelemetrySample (frozen dataclass)
│   └── generators/
│       └── obd_generator.py     # Physics-inspired OBD-II-style telemetry simulator
├── analytics/
│   ├── engine/
│   │   └── analytics_engine.py  # Central coordinator: consumes samples → produces snapshots
│   ├── behaviour/
│   │   ├── detection/
│   │   │   └── analyzer.py      # DriverBehaviourAnalyzer — point-in-time behaviour flags
│   │   ├── events/
│   │   │   ├── tracker.py       # BehaviourEventTracker — start/end temporal events
│   │   │   └── event.py         # BehaviourEvent dataclass
│   │   └── aggregation/
│   │       ├── summarizer.py    # DriverBehaviourSummarizer — trip-level rollup
│   │       └── summary.py       # DriverBehaviourSummary dataclass
│   ├── context/
│   │   ├── analytics_context.py # Immutable per-trip context (route, driver, vehicle metadata)
│   │   └── context_store.py     # Keyed store of AnalyticsContext
│   ├── state/
│   │   ├── runtime_state.py     # Mutable per-vehicle operational state
│   │   └── runtime_state_store.py # Keyed store of RuntimeState
│   ├── input/
│   │   └── analysis_input.py    # Normalized input envelope for analyzers
│   ├── snapshot/
│   │   ├── analytics_snapshot.py # AnalyticsSnapshot dataclass
│   │   └── snapshot_store.py    # Keyed store of AnalyticsSnapshot
│   ├── vehicle_health/
│   │   ├── vehicle_health_engine.py # Coordinates 5 subsystem analyzers
│   │   └── analyzers/           # Engine, Brake, Cooling, Transmission, FuelSystem
│   └── driver_statistics/
│       ├── driver_statistics_engine.py # Aggregates completed trips into driver stats
│       ├── safety.py            # Canonical safety score + grade computation
│       ├── config.py            # Constants (weights, thresholds, severity vocabulary)
│       └── aggregators/
│           └── driver_score_calculator.py # Stub (NotImplementedError)
├── maintenance/
│   ├── maintenance_service.py   # Orchestrates 5 estimators, dedupes + sorts recommendations
│   ├── models/
│   │   ├── maintenance_type.py  # 14 maintenance types
│   │   ├── maintenance_recommendation.py
│   │   └── maintenance_record.py
│   ├── maintenance_config.py    # Priority/severity thresholds, service profiles
│   ├── estimation/
│   │   └── rules.py             # Pure functions: health_factor, interval_remaining_km, etc.
│   └── estimators/
│       ├── component_estimator.py # Shared base with emit rules
│       ├── engine_estimator.py
│       ├── brake_estimator.py
│       ├── cooling_estimator.py
│       ├── transmission_estimator.py
│       └── fuel_system_estimator.py
├── alerts/
│   ├── alert_engine.py          # Orchestrates generators, deduplicates, sorts
│   ├── models/
│   │   └── fleet_alert.py       # Frozen FleetAlert dataclass + enums
│   ├── generators/              # AlertContext + 4 generators (health, telemetry, maintenance, trip)
│   ├── deduplication.py         # DuplicateSuppressor with cooldown window
│   └── alerts_config.py         # AlertConfig + severity ranks
├── db/
│   ├── session.py               # Async session factory (asyncpg)
│   ├── base.py                  # DeclarativeBase
│   ├── models/                  # ~12 SQLAlchemy models
│   ├── repositories/            # One repository per aggregate
│   ├── persistence_service.py   # Single facade for all DB writes
│   └── migrations/              # Alembic environment
├── streaming/
│   └── snapshot_stream.py       # AnalyticsSnapshotStream — sync pub/sub
├── dashboard/
│   └── services/
│       └── dashboard_builder.py # Merges state into DashboardSnapshot
├── trips/
│   ├── schemas/
│   │   └── trip_payload.py      # TripSnapshot + TripsSnapshot dataclasses
│   ├── services/
│   │   ├── trip_builder.py      # Builds completed-trip snapshots
│   │   └── active_trip_builder.py # Builds active-trip snapshots
│   └── store/
│       └── trip_store.py        # In-memory dict of completed trips
└── config.py                    # Empty placeholder
```

---

## 3. Module Specifications

### 3.1 `backend/api/main.py` — FastAPI App

- **Purpose:** Compose the runtime, publishers, workers, and WebSocket managers into a running FastAPI application.
- **Responsibilities:** Define lifespan (startup/shutdown), register routers, configure CORS.
- **Inputs:** None (module-level singletons).
- **Outputs:** FastAPI app instance.
- **Dependencies:** `DriveVitalsRuntime`, publishers, workers, routers.
- **External flow:** Served by Uvicorn; clients connect via HTTP and WebSocket.

### 3.2 `backend/application/runtime.py` — DriveVitalsRuntime

- **Purpose:** Central orchestrator. Owns the lifetime of every subsystem and drives the telemetry-producing loop.
- **Responsibilities:** construct and hold instances; wire consumers into the telemetry pipeline; drive the main tick loop; own trip-completion logic.
- **Inputs:** `PersistenceService` (optional).
- **Outputs:** None directly; drives all downstream consumers via the telemetry sink.
- **Dependencies:** All engines, consumers, pipeline, stores, publishers.
- **Internal flow:** constructed → `_configure_fleet()` → `run()` enters tick loop.
- **External flow:** FastAPI lifespan calls `run()`/`stop()`.

### 3.3 `backend/pipeline/telemetry_pipeline.py` — TelemetryPipeline

- **Purpose:** Fan-out point for every telemetry sample to every interested consumer.
- **Responsibilities:** Define `TelemetryConsumer` protocol; register/unregister; publish samples with consumer isolation.
- **Inputs:** `TelemetrySample`.
- **Outputs:** forwards the same sample to each registered consumer.
- **Dependencies:** `TelemetrySample`, consumer protocol.
- **Internal flow:** `register(consumer)` adds to a list; `publish(sample)` iterates and calls `consumer.consume(sample)`, catching and logging per-consumer failures.
- **External flow:** called by `FleetRunner.tick_all()` sink.

### 3.4 `backend/fleet/runtime/fleet_runner.py` — FleetRunner

- **Purpose:** Timekeeper + dispatcher for the simulated fleet.
- **Responsibilities:** own `VehicleRunner`s; `tick_all()` advances each vehicle one step; forward each `TelemetrySample` to a caller-provided sink.
- **Inputs:** `VehicleRunner` instances, tick clock.
- **Outputs:** `TelemetrySample` per vehicle per tick.
- **Dependencies:** `VehicleRunner`, `TelemetrySink` callable. No direct analytics / DB / WebSocket coupling.
- **External flow:** runtime loop calls `tick_all()`.

### 3.5 `backend/fleet/runtime/vehicle_runner.py` — VehicleRunner

- **Purpose:** One simulated vehicle.
- **Responsibilities:** model the vehicle's physics/state machine; progress a trip; emit one `TelemetrySample` per `tick()`.
- **Inputs:** `Vehicle`, `Driver`, `Route` (assignment), `OBDGenerator`.
- **Outputs:** `TelemetrySample`.
- **Dependencies:** `TelemetrySample`, `OBDGenerator`, route/vehicle/driver models.
- **External flow:** called once per second by `FleetRunner.tick_all()`.

### 3.6 `backend/fleet/config/fleet_factory.py` — FleetFactory

- **Purpose:** Deterministic fixture generation for the simulated fleet.
- **Responsibilities:** build 6 `Vehicle`, 6 `Driver`, 6 `Route`, 6 `DriverAssignment` instances.
- **Inputs:** none (module-level data/constants).
- **Outputs:** model instances.
- **External flow:** consumed by `DriveVitalsRuntime`.

### 3.7 `backend/telemetry/models/telemetry_sample.py` — TelemetrySample

- **Purpose:** the canonical telemetry schema (frozen dataclass).
- **Responsibilities:** define one sample: vehicle id, timestamp, speed, rpm, throttle, coolant temp, engine load, fuel rate/level, odometer.
- **Outputs:** used by pipeline, analytics, persistence, alerts, maintenance, dashboard.
- **Dependencies:** none (pure dataclass).

### 3.8 `backend/telemetry/generators/obd_generator.py` — OBDGenerator

- **Purpose:** Simulates raw OBD-II style reads feeding the `VehicleRunner` physics.
- **Responsibilities:** Stands in for ELM327 hardware until real adoption.
- **Inputs:** behaviour profile, seed, route, runtime state.
- **Outputs:** `TelemetrySample`, distance delta, fuel delta.

### 3.9 `backend/analytics/engine/analytics_engine.py` — AnalyticsEngine

- **Purpose:** Central telemetry consumer; turns raw telemetry into per-driver behaviour state and per-vehicle snapshots.
- **Responsibilities:** consume samples; maintain runtime state; run behaviour analysis; track events; emit snapshots.
- **Inputs:** `TelemetrySample`.
- **Outputs:** `AnalyticsSnapshot` (to snapshot stream subscribers); derived state.
- **Internal flow:** `Telemetry → Runtime State → Analysis Input → Driver Behaviour Analysis → Behaviour Events → Trip-Level Behaviour Summary → Snapshot`.

### 3.10 `backend/analytics/vehicle_health/` — Vehicle Health

- **Purpose:** Per-vehicle health scoring from a rolling telemetry window.
- **Responsibilities:** Maintain 20-sample deques; run 5 analyzers; produce weighted overall health status.
- **Members:** `VehicleHealthEngine`, 5 component analyzers, `HealthConfig`, `HealthStatus` enum.

### 3.11 `backend/maintenance/` — Maintenance

- **Purpose:** Project-based maintenance recommendations per vehicle.
- **Responsibilities:** Compute interval-based recommendations, derive priority/severity, estimate cost + due date.
- **Members:** 14 `MaintenanceType` enum values, `MaintenanceRecommendation`, `MaintenanceRecord`, `PriorityThresholds`, `SeverityThresholds`, 5 estimators, `MaintenanceService`.

### 3.12 `backend/alerts/` — Alert Subsystem

- **Purpose:** Unified alert model + generation framework.
- **Responsibilities:** Generate alerts from health, telemetry, maintenance, and trip data; deduplicate within cooldown windows; resolve cleared alerts.
- **Members:** `FleetAlert` model, `AlertEngine`, 4 generators, `DuplicateSuppressor`.

### 3.13 `backend/trips/` — Trip Snapshots

- **Purpose:** Assemble canonical trip snapshots for both completed and active trips.
- **Responsibilities:** `TripBuilder` builds final trip metrics from completed-trip data; `build_active_trip_snapshot()` builds live snapshots from runtime state; `TripStore` caches completed trips.
- **Members:** `TripSnapshot`, `TripsSnapshot`, `TripBuilder`, `build_active_trip_snapshot()`, `TripStore`.

### 3.14 `backend/db/` — Persistence Layer

- **Purpose:** The active database layer.
- **Responsibilities:** Async SQLAlchemy ORM, repository pattern, `PersistenceService` facade, Alembic migrations.
- **Members:** ~12 models, 10 repositories, `PersistenceService`.

---

## 4. Module Interaction

The backend modules communicate according to the following flow:

```text
FleetRunner.tick_all()
    ↓
TelemetrySample(s)
    ↓
TelemetryPipeline.publish()        [fan-out]
    ↓
    ├─ AnalyticsEngine.consume()
    │     ↓
    │   AnalyticsSnapshot
    │     ↓
    │   AnalyticsSnapshotStream
    │     ↓
    │   DashboardSnapshotPublisher → snapshot_queue → snapshot_worker → WebSocketManager → /ws/dashboard
    │     ↓
    │   TripSnapshotPublisher → trips_queue → trips_worker → WebSocketManager → /ws/trips
    │
    ├─ PersistenceTelemetryConsumer
    │     ↓
    │   persist_telemetry → DB
    │   persist_vehicle_health → DB
    │   generate_alerts → persist_alerts → DB
    │
    └─ (future consumers)
```

REST API requests are handled independently through the API module, which communicates with repositories before accessing the database.

---

## 5. Design Principles

The backend follows these software engineering principles:

- **Modular Architecture:** Each component performs one primary responsibility.
- **Separation of Concerns:** Telemetry generation, analytics, persistence, and transport are independent layers.
- **Single Responsibility:** One module, one job.
- **Loose Coupling:** Connected via protocols (e.g. `TelemetryConsumer`) and streams, not hard imports.
- **High Cohesion:** Related code lives together (e.g. all health analyzers in `vehicle_health/`).
- **Scalability:** The pipeline and pub/sub patterns allow new consumers without modifying existing ones.
- **Reusability:** Pure functions and frozen dataclasses are used wherever possible.
- **Maintainability:** Explicit naming, docstrings, and clear boundaries between layers.

---

## 6. Future Extensions

The backend architecture has been designed to support future enhancements without major structural changes.

Planned future additions include:

- Real OBD-II communication (replacing `OBDGenerator`)
- Machine learning inference service
- Predictive maintenance engine
- Driver authentication
- GPS tracking
- Diagnostic Trouble Code (DTC) processing
- Fleet maintenance scheduler
- Cloud deployment
- Microservice decomposition
- Computer vision integration

These additions can be incorporated while preserving the existing modular architecture.
