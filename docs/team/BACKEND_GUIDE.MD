# Backend Guide — DriveVitals

This is a practical guide to the current backend implementation: what each part does and how data moves from the fleet runtime to connected dashboard clients.

## Architecture Diagram

```mermaid
graph TD
    subgraph Runtime["Runtime (no FastAPI, no WebSockets)"]
        A[DriveVitalsRuntime] --> B[FleetRunner]
        B --> C[TelemetrySample]
        C --> D[TelemetryPipeline]
        D --> E[AnalyticsEngine]
        E --> F[AnalyticsSnapshot]
        F --> G[AnalyticsSnapshotStream]
    end

    subgraph FastAPI["FastAPI integration layer"]
        H[DashboardSnapshotPublisher] --> I[snapshot_queue]
        I --> J[snapshot_worker]
        K[TripSnapshotPublisher] --> L[trips_queue]
        L --> M[trips_worker]
        J --> N[WebSocketManager]
        M --> N
    end

    G --> H
    A --> K
    N --> O[/ws/dashboard clients]
    N --> P[/ws/trips clients]

    subgraph REST["REST API"]
        Q[10 routers /api/v1]
    end

    A --> Q
```

## Folder Responsibilities

Based on the modules currently imported and implemented:

| Folder | Responsibility |
|--------|----------------|
| `backend/api/` | FastAPI composition: `main.py` (app + lifespan), `v1/routers/` (10 REST routers), `websocket/` (WebSocket routes, payload building, workers, managers). |
| `backend/application/` | `runtime.py` — `DriveVitalsRuntime`, the composition root that wires every subsystem together and drives the main loop. Framework-independent. |
| `backend/fleet/` | Fleet domain: `config/fleet_factory.py` (fixture generation), `models/` (Vehicle, Driver, Route, Trip, Assignment), `runtime/` (FleetRunner, VehicleRunner). |
| `backend/pipeline/` | `TelemetryPipeline` — fan-out dispatcher that forwards each `TelemetrySample` to every registered consumer. |
| `backend/analytics/` | Analytics domain: `engine/` (AnalyticsEngine), `behaviour/` (detection, event tracking, summarization), `context/` (AnalyticsContext + store), `state/` (RuntimeState + store), `snapshot/` (AnalyticsSnapshot + store), `vehicle_health/` (5 subsystem analyzers), `driver_statistics/` (aggregation + scoring). |
| `backend/maintenance/` | Maintenance recommendation subsystem: 5 estimators + `MaintenanceService`. |
| `backend/alerts/` | Alert model + generators (health, telemetry, maintenance, trip) + `AlertEngine` with deduplication. |
| `backend/telemetry/` | `TelemetrySample` (canonical frozen dataclass) + `OBDGenerator` (simulated telemetry source). |
| `backend/application/consumers/` | `VehicleHealthConsumer` and `DriverStatisticsConsumer` — pipeline consumers that bridge telemetry to health and driver-statistics engines. |
| `backend/trips/` | Trip snapshot assembly: `TripBuilder` (completed trips), `build_active_trip_snapshot()` (active trips), `TripStore` (in-memory completed-trip cache), `TripSnapshot` / `TripsSnapshot` contracts. |
| `backend/db/` | SQLAlchemy async models, repositories, `PersistenceService`, Alembic migrations. |
| `backend/streaming/` | `AnalyticsSnapshotStream` — synchronous pub/sub for analytics snapshots. |
| `backend/dashboard/` | `DashboardBuilder` — merges runtime state, health, and trip data into a `DashboardSnapshot`. |

## Application Startup

`backend/api/main.py` creates module-level singletons. On FastAPI `lifespan` startup it:

1. Subscribes `snapshot_publisher` to `runtime.snapshot_stream`.
2. Registers `_trip_flush` and `_trip_update` callbacks on the runtime.
3. Starts `snapshot_worker()` and `trips_worker()` as background `asyncio.Task`s.
4. Starts `runtime.run()` as a background `asyncio.Task`.

On shutdown, it stops the runtime, cancels all tasks, and unsubscribes the publisher — in that order.

## DriveVitalsRuntime

`backend/application/runtime.py`. Composes and owns:

- `FleetRunner` (`_fleet`)
- `TelemetryPipeline` (`_telemetry_pipeline`)
- Analytics dependencies: `RuntimeStateStore`, `AnalyticsContextStore`, `DriverBehaviourAnalyzer`, `BehaviourEventTracker`, `DriverBehaviourSummarizer`, `AnalyticsSnapshotStore`
- `AnalyticsSnapshotStream` (`_snapshot_stream`)
- `AnalyticsEngine` (`_analytics_engine`), built from all of the above
- `VehicleHealthEngine` + `VehicleHealthConsumer`
- `DriverStatisticsEngine` + `DriverStatisticsConsumer`
- `MaintenanceService`
- `AlertEngine`
- `IntelligenceState` (shared health/statistics state for consumers)

At construction, it registers the analytics engine and vehicle health consumer with the telemetry pipeline, loads fleet configuration via `FleetFactory.from_config()`, and builds an `AnalyticsContext` per assignment.

Its docstring is explicit that the runtime does not know about FastAPI, WebSockets, frontend clients, or HTTP routes.

### `run()` flow

1. Persist reference data (vehicles, drivers, routes).
2. Abort stale `in_progress` trips from previous sessions.
3. Persist new trip rows (before telemetry starts, to satisfy FK constraints).
4. Start all trips.
5. Enter the fleet tick loop:
   - `FleetRunner.tick_all()` → samples
   - For each sample: `TelemetryPipeline.publish(sample)`
   - Detect vehicles that completed this tick
   - Handle trip completions (flush analytics, driver stats, maintenance, alerts, persistence callbacks)
   - Publish active-trip updates
   - `await asyncio.sleep(tick_seconds)`

### `stop()`

Sets `_running = False`. The loop ends on its next iteration.

## FleetRunner

Ticks all configured vehicle assignments each cycle and returns the `TelemetrySample`s produced (`tick_all`). `start_all` begins all runners; `active_runners()` reports whether any are still running, which gates the runtime loop.

## VehicleRunner

Represents one active vehicle performing a trip. Owns the temporary `RuntimeState` for that vehicle and drives the OBD generator tick by tick, updating the persistent `Vehicle` (odometer, fuel level) and the `Trip` (distance travelled, lifecycle status).

Key methods:

- `start(now)` — transitions trip to `STARTED`, starts engine, resets runtime state.
- `tick(now)` — advances simulation by one tick, returns a `TelemetrySample`. Raises if the trip is already completed.
- `is_complete()` — returns `True` when `trip.status == COMPLETED`.

## TelemetryPipeline

Receives each `TelemetrySample` published by the runtime and dispatches it to registered consumers. Currently, `AnalyticsEngine` and `_PersistenceTelemetryConsumer` (inline in `runtime.py`) are registered.

## AnalyticsEngine

Consumes telemetry samples and, using its collaborators (`RuntimeStateStore`, `AnalyticsContextStore`, `DriverBehaviourAnalyzer`, `BehaviourEventTracker`, `DriverBehaviourSummarizer`, `AnalyticsSnapshotStore`), produces `AnalyticsSnapshot`s and emits them onto `AnalyticsSnapshotStream`.

## AnalyticsSnapshot

The data contract produced by the analytics engine, holding `vehicle_id`, `driver_id`, `trip_id`, `timestamp`, `telemetry`, `behaviour`, `completed_events`, and `active_event_types`.

## AnalyticsSnapshotStream

A synchronous publish/subscribe stream. `AnalyticsEngine` publishes snapshots onto it; the FastAPI layer subscribes publishers to it. This is the decoupling boundary between analytics and any application-layer consumer.

## DashboardSnapshotPublisher

`backend/api/websocket/snapshot_publisher.py`. A subscriber to `AnalyticsSnapshotStream`. Its `publish(snapshot)` method calls `queue.put_nowait(snapshot)`. This is the sync-to-async adaptation point.

## TripSnapshotPublisher

`backend/api/websocket/trip_publisher.py`. Called from runtime callbacks. Builds `TripSnapshot`s via `TripBuilder`, stores them in `TripStore`, aggregates totals, and publishes `TripsSnapshot` to `trips_queue`. Also exposes `publish_active()` for per-tick active-trip broadcasts.

## Snapshot Workers

`snapshot_worker` and `trips_worker` are async loops that pop snapshots from their queues, serialize them, and broadcast via `WebSocketManager.broadcast()`.

## WebSocketManager

`backend/api/websocket/manager.py`. A single shared instance (`websocket_manager` in `dependencies.py`) owns:

- `connect(websocket)` — accepts and stores a connection.
- `disconnect(websocket)` — removes a connection if present.
- `broadcast(message)` — sends `message` as JSON to every active connection; removes any connection that raises during send.
- `connection_count` — number of currently active connections.

## Persistence

`PersistenceService` is the single entry point for all database access. It wraps 10 repository classes and writes data incrementally as it is produced. The runtime registers an inline `_PersistenceTelemetryConsumer` and `_PersistenceSnapshotSubscriber` to feed telemetry, health, alerts, and behaviour events into persistence without coupling the runtime to SQLAlchemy directly.

## Stale-Trip Recovery

At startup, `persistence.abort_stale_trips()` marks every `in_progress` trip as `aborted`. This ensures that trips created by a previous runtime session are never reported as active. History, recorded metrics, and telemetry are preserved.

## Architecture Rules

- No WebSocket code inside the runtime (`DriveVitalsRuntime`, `FleetRunner`, `TelemetryPipeline`, `AnalyticsEngine`). These modules must remain importable and runnable without FastAPI or Starlette.
- No FastAPI dependencies inside `backend/analytics/`.
- No dashboard-specific logic inside `AnalyticsEngine` — it produces `AnalyticsSnapshot`s and publishes to `AnalyticsSnapshotStream`; it does not know about dashboards, JSON payloads, or clients.
- No business logic inside the WebSocket routes — they only manage connection accept/receive/disconnect via `WebSocketManager`.
- Connection management belongs to `WebSocketManager` alone.
- Snapshot-to-async adaptation belongs to publishers and `asyncio.Queue` boundaries.
