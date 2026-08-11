# High-Level Architecture

DriveVitals is designed as a modular, layered, and scalable system that transforms raw vehicle telemetry into actionable insights for drivers and fleet operators. The architecture follows a data pipeline approach where each layer is responsible for a specific stage of processing, from data acquisition to visualization and analytics.

**Current state:** The system uses a **physics-inspired simulator** (`OBDGenerator` + `VehicleRunner`) to produce OBD-II-style telemetry. Real OBD-II / CAN bus integration is a roadmap item, not the current data source.

---

## 1. System Overview

The system is divided into five main layers:

1. **Telemetry Source** (simulated OBD-II generator)
2. **Fleet Runtime** (tick-driven simulation orchestration)
3. **Telemetry Pipeline** (fan-out dispatch to consumers)
4. **Analytics Layer** (behaviour, health, maintenance, alerts)
5. **Data Storage & API Layer** (PostgreSQL, REST, WebSockets)
6. **Presentation Layer** (React dashboard)

---

## 2. High-Level Architecture Diagram

```
Simulated OBD-II Generator (OBDGenerator)
       ↓
VehicleRunner  (per-vehicle physics + driver profile)
       ↓
FleetRunner.tick_all()  (advances every active vehicle for one tick)
       ↓
TelemetryPipeline.publish()  (fan-out to all registered consumers)
       ↓
    ┌────────────────────┬─────────────────────┐
    ↓                     ↓                     ↓
AnalyticsEngine   VehicleHealthConsumer   Persistence consumer
    ↓                     ↓                     ↓
Behaviour events   HealthSnapshot         telemetry_samples row
    ↓                     ↓
Trip-level         MaintenanceService
behaviour summary  (on health change)
    ↓                     ↓
AnalyticsSnapshot   MaintenanceRecommendation
    ↓                     ↓
AnalyticsSnapshotStream  AlertEngine → FleetAlert
    ↓
DashboardBuilder → DashboardSnapshot
    ↓
asyncio.Queue → snapshot_worker → WebSocketManager.broadcast
    ↓
/ws/dashboard clients (React dashboard)
```

---

## 3. Layer Descriptions

### 3.1 Telemetry Source

- Implemented as `OBDGenerator` inside `backend/telemetry/generators/`.
- Produces per-tick OBD-II-style samples (speed, RPM, throttle, brake pressure, coolant temp, engine load, fuel rate/level, odometer).
- Uses a seeded random number generator for deterministic, reproducible simulation.
- Driver behaviour profiles (city, highway, aggressive, eco) shape throttle/brake patterns.
- **Future:** A real OBD-II / CAN bus source can replace this generator without changing downstream consumers.

### 3.2 Fleet Runtime

- Implemented in `backend/fleet/runtime/`.
- `FleetRunner` coordinates multiple `VehicleRunner` instances.
- Each `VehicleRunner` advances one vehicle's state by one tick and emits an immutable `TelemetrySample`.
- The runtime loop (`DriveVitalsRuntime.run()`) ticks all active vehicles once per second.

### 3.3 Telemetry Pipeline

- Implemented in `backend/pipeline/telemetry_pipeline.py`.
- A simple `register()`/`publish()` fan-out — it has no knowledge of what its consumers do with a sample.
- Decouples telemetry production from every downstream consumer.

### 3.4 Analytics Layer

- Implemented in `backend/analytics/`.
- **Driver Behaviour:** `DriverBehaviourAnalyzer` evaluates each sample against configurable thresholds. `BehaviourEventTracker` converts point-in-time detections into temporal events. `DriverBehaviourSummarizer` rolls up events into per-trip summaries.
- **Vehicle Health:** `VehicleHealthEngine` coordinates five independent `SubsystemHealthAnalyzer` implementations (engine, brake, cooling, transmission, fuel system), each producing scores from a rolling telemetry window.
- **Maintenance:** `MaintenanceService` merges five `MaintenanceEstimator` outputs into prioritized recommendations with interval-based scheduling.
- **Alerts:** `AlertEngine` orchestrates four generators (health, telemetry, maintenance, trip) with deduplication and stale-alert resolution.
- **Driver Statistics:** `DriverStatisticsEngine` aggregates completed-trip behaviour summaries into standing per-driver statistics.

### 3.5 Data Storage & API Layer

- **Persistence:** PostgreSQL 16 via async SQLAlchemy (`asyncpg`) and Alembic migrations. `PersistenceService` is the single entry point for all database access.
- **REST API:** 10 versioned routers under `/api/v1` providing read access to vehicles, drivers, routes, trips, telemetry, health, statistics, maintenance, alerts, and system status. Alerts also support `POST` acknowledge/resolve.
- **WebSockets:** Two channels — `/ws/dashboard` (fleet snapshots) and `/ws/trips` (trip snapshots). Both are server-push only.

### 3.6 Presentation Layer

- React 18 + Vite SPA.
- Subscribes to WebSocket channels for live data.
- Hydrates historical data via REST API calls.
- Pages: Dashboard, Fleet, Vehicle Health, Drivers, Trips, Maintenance, Alerts, Live Telemetry, Analytics, Settings.

---

## 4. Communication Flow

1. `FleetRunner.tick_all()` advances every active vehicle and produces `TelemetrySample`s.
2. `TelemetryPipeline.publish(sample)` dispatches each sample to registered consumers.
3. `AnalyticsEngine` updates runtime state, runs behaviour analysis, tracks events, and emits `AnalyticsSnapshot`s.
4. `VehicleHealthConsumer` folds samples into rolling health windows.
5. `DashboardSnapshotPublisher` and `TripSnapshotPublisher` bridge snapshots to WebSocket queues.
6. WebSocket workers broadcast snapshots to connected dashboard clients.
7. `PersistenceService` writes telemetry, health, behaviour events, trips, maintenance records, and alerts to PostgreSQL incrementally.

---

## 5. Core Design Principles

### Modular Design

Each system component (telemetry, analytics, storage, UI) is independently developed and replaceable.

### Real-Time Processing

Telemetry is processed in near real-time to enable live monitoring and alerts.

### Scalability

Architecture supports expansion to multiple vehicles (fleet systems) and future cloud deployment. The current implementation runs 6 vehicles in a single asyncio event loop.

### Extensibility

Designed to support future integration of:

- Machine Learning models
- Predictive maintenance systems
- Real OBD-II / CAN bus hardware
- Mobile applications
- Cloud analytics platforms

### Determinism

Given the same seed and configuration, the same simulation run is reproducible. This is enforced by seeding per-vehicle RNGs from the simulation `run_id`.

### Source-Agnostic Telemetry

Everything downstream of `TelemetryPipeline` is source-agnostic. A real OBD-II source can replace the simulator without touching analytics, health, maintenance, or dashboard logic.
