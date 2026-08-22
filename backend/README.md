# DriveVitals Backend

This document covers the DriveVitals backend architecture, setup, and development workflow. Every path, class, and behavior described here reflects the actual code in this repository.

## Stack

- **Language**: Python 3.12+ (CI runs on 3.13)
- **Framework**: FastAPI (async HTTP + WebSocket server)
- **Database**: PostgreSQL 16 (persistent vehicle/driver/fleet state)
- **ORM**: SQLAlchemy 2.x async (`asyncpg` driver)
- **Migrations**: Alembic (schema versioning)
- **WebSockets**: native FastAPI WebSocket support
- **Testing**: pytest with `pytest-asyncio` (async mode) and `httpx`

## Architecture Overview

The backend follows a layered, responsibility-driven structure:

```
backend/
├── api/                          # Integration layer (no business logic)
│   ├── main.py                   # FastAPI app factory, lifespan wiring, CORS
│   ├── dependencies.py           # Shared singletons (e.g. WebSocketManager)
│   ├── v1/                       # Versioned REST API mounted under /api/v1
│   │   ├── routers/              # One router per domain (vehicles, drivers,
│   │   │                         #   routes, trips, telemetry, vehicle_health,
│   │   │                         #   driver_statistics, maintenance, alerts,
│   │   │                         #   analytics, system)
│   │   ├── schemas/              # Pydantic request/response schemas
│   │   └── services/             # Read services backing the routers
│   └── websocket/                # WebSocket channels + broadcast workers
│       ├── dashboard.py          # /ws/dashboard endpoint + snapshot_worker
│       ├── trips.py              # /ws/trips endpoint + trips_worker
│       ├── alerts.py             # /ws/alerts endpoint + alerts_worker
│       ├── manager.py            # WebSocketManager (shared broadcast bus)
│       ├── snapshot_publisher.py # Dashboard queue publisher
│       └── trip_publisher.py     # Trips queue publisher
│
├── application/                  # Composition root & orchestration
│   ├── runtime.py                # DriveVitalsRuntime — main tick loop, wires
│   │                             #   engines, owns trip-completion logic
│   ├── consumers/                # Pipeline consumers (vehicle health,
│   │                             #   driver statistics)
│   ├── intelligence_state.py     # In-memory intelligence state holder
│   └── driver_statistics_reconciler.py
│
├── fleet/                        # Simulated world: domain models + runtime
│   ├── models/                   # Vehicle, Driver, Route, Trip, Assignment
│   ├── config/                   # Fleet configuration + factory
│   └── runtime/                  # FleetRunner, VehicleRunner, runtime state
│
├── telemetry/                    # Telemetry production (simulation only)
│   ├── generators/
│   │   └── obd_generator.py      # OBDGenerator — per-tick OBD-style samples
│   └── models/
│       └── telemetry_sample.py   # Immutable TelemetrySample
│
├── pipeline/
│   └── telemetry_pipeline.py     # Fan-out dispatch of each sample to consumers
│
├── analytics/                    # Rule-based analysis (no ML)
│   ├── engine/                   # AnalyticsEngine (driver behaviour)
│   ├── behaviour/                # Event detection, tracking, aggregation/scoring
│   ├── vehicle_health/           # VehicleHealthEngine + 5 subsystem analyzers
│   ├── driver_statistics/        # Per-driver aggregation over completed trips
│   ├── trip/                     # Trip-level analysis and summaries
│   ├── vehicle/, fleet/          # Vehicle/fleet-level analysis helpers
│   ├── rules/                    # Configurable threshold rule definitions
│   ├── context/, state/          # Trip context vs. mutable runtime state stores
│   └── snapshot/                 # AnalyticsSnapshot output type + store
│
├── maintenance/                  # MaintenanceService + subsystem estimators
├── alerts/                       # AlertEngine + 4 generators + deduplication
│
├── streaming/                    # AnalyticsSnapshotStream pub/sub
│
├── dashboard/                    # Frontend-facing dashboard assembly
│   ├── services/dashboard_builder.py
│   ├── mapper.py
│   ├── models/                   # DashboardSnapshot, VehicleDashboardSummary…
│   └── schemas/dashboard_payload.py
│
├── trips/                        # Trip snapshot assembly
│   ├── services/                 # TripBuilder, ActiveTripBuilder
│   ├── store/trip_store.py
│   └── schemas/trip_payload.py   # TripsSnapshot / TripSnapshot
│
├── db/                           # Persistence layer (repository pattern)
│   ├── session.py                # Async engine + session factory
│   ├── persistence_service.py    # Single facade over all repositories
│   ├── repositories/             # One repository per aggregate
│   ├── models/                   # SQLAlchemy ORM models
│   └── migrations/               # Alembic migration scripts
│
└── shared/, utils/               # Enums, exceptions, logging, helpers
```

## Key Components

**DriveVitalsRuntime** (`application/runtime.py`)
- Composition root; wires every engine and registers pipeline consumers
- Drives the main simulation tick loop and trip lifecycle
- Owns trip-completion logic: final scoring, persistence, driver statistics, maintenance estimation, alert generation

**FleetRunner / VehicleRunner** (`fleet/runtime/`)
- `VehicleRunner` advances one vehicle/driver/route assignment by one tick and emits a `TelemetrySample`
- `FleetRunner` ticks every active assignment per simulation step

**OBDGenerator** (`telemetry/generators/obd_generator.py`)
- Stateful, per-tick generator producing OBD-II-style measurements (speed, RPM, throttle, brake pressure, coolant temperature, engine load, fuel rate/level, odometer)
- Uses bounded per-tick random variation (`random.Random`) shaped by driver behaviour profiles (STANDARD / ECO / CAUTIOUS / AGGRESSIVE) and route types (URBAN / HIGHWAY / RURAL), with internal-consistency rules: speed changes are bounded per tick, RPM is derived from speed via a simple gear model, fuel rate scales with engine load, coolant warms gradually toward operating temperature
- This is **not** an Ornstein-Uhlenbeck process or any stochastic differential equation — it is bounded random noise plus deterministic derived relationships. An OU-based noise model exists only as design intent in `docs/design/DigitalTwinArchitecture/04_vehicle_simulation_mode.md` and is not implemented.
- No real OBD-II/CAN hardware is used anywhere; the generator only emits raw measurements, never analytics conclusions

**TelemetryPipeline** (`pipeline/telemetry_pipeline.py`)
- Thin fan-out dispatcher: every registered consumer receives every sample independently

**Analytics Engines** (all rule-based, no machine learning)
- **AnalyticsEngine** (`analytics/engine/`, `analytics/behaviour/`): detects speeding, harsh braking, aggressive throttle, and high-RPM events against configurable thresholds plus route context; aggregates events per trip into a 0–100 safety score
- **VehicleHealthEngine** (`analytics/vehicle_health/`): five subsystem analyzers (engine, brake, cooling, transmission, fuel system) produce a combined health snapshot from a rolling telemetry window
- **DriverStatisticsEngine** (`analytics/driver_statistics/`): aggregates completed-trip behaviour into standing per-driver statistics, updated once per trip completion
- **MaintenanceService** (`maintenance/`): five estimators mirror the health subsystems and produce prioritized maintenance recommendations
- **AlertEngine** (`alerts/`): four generator families (health, telemetry, maintenance, trip) with deduplication

**Persistence Layer** (`db/`)
- Repository pattern: one repository per aggregate, all accessed through `PersistenceService`
- Async SQLAlchemy sessions over `asyncpg`; Alembic manages schema versioning
- Trip rows are written before telemetry begins (foreign-key ordering constraint) and completed at trip end

## Running Locally

### Prerequisites

- Python 3.12+
- PostgreSQL 16 running on `localhost:5432` (the root `docker-compose.yml` provisions one: `docker compose up -d`)
- A `.env` file at the repository root (copy `.env.example`); `POSTGRES_PASSWORD` is required, other variables have defaults

### Setup

```bash
# From the repository root
python -m venv .venv
.venv\Scripts\activate          # Windows (bash: source .venv/bin/activate)

pip install -r requirements.txt

# Apply database migrations (run from backend/)
cd backend
alembic upgrade head

# Start the API (from the repository root)
cd ..
uvicorn backend.api.main:app --reload
```

The FastAPI server starts on `http://localhost:8000`; `GET /` returns a status payload.

### Configuration

Environment variables read by `backend/db/session.py`:

| Variable | Default | Purpose |
|----------|---------|---------|
| `POSTGRES_USER` | `postgres` | Database user |
| `POSTGRES_PASSWORD` | *(required)* | Database password |
| `POSTGRES_DB` | `drivevitals_dev` | Database name |
| `POSTGRES_HOST` | `localhost` | Database host |
| `POSTGRES_PORT` | `5432` | Database port |

## Testing

Tests live at the **repository root** in `tests/`, organized in three layers:

```
tests/
├── unit/           # Pure logic tests (runtime, analytics, scoring)
├── integration/    # Multi-layer tests (fleet runtime, consumers, persistence)
└── api/            # FastAPI endpoint tests (HTTP + WebSocket), one file per router
```

Run from the repository root:

```bash
pytest              # full suite (integration/api tests need PostgreSQL configured)
pytest tests/unit   # unit tests only (no DB required)
pytest -v           # verbose
```

Configuration lives in `pytest.ini` (`testpaths = tests`, `asyncio_mode = auto`). CI (`.github/workflows/ci.yml`) provisions a PostgreSQL 16 service container, runs `alembic upgrade head` from `backend/`, then `pytest -v`.

## REST API

All REST routes are versioned under `/api/v1`. Routers (defined in `backend/api/v1/routers/`):

| Router | Prefix | Methods |
|--------|--------|---------|
| vehicles | `/api/v1/vehicles` | GET |
| drivers | `/api/v1/drivers` | GET |
| routes | `/api/v1/routes` | GET |
| trips | `/api/v1/trips` | GET, DELETE |
| telemetry | `/api/v1/telemetry` | GET |
| vehicle-health | `/api/v1/vehicle-health` | GET |
| driver-statistics | `/api/v1/driver-statistics` | GET |
| maintenance | `/api/v1/maintenance` | GET, PATCH |
| alerts | `/api/v1/alerts` | GET, POST (acknowledge/resolve) |
| analytics | `/api/v1/analytics` | GET |
| system | `/api/v1/system` | GET |

See `docs/API.md` for the full endpoint specification.

## WebSocket Channels

Three WebSocket endpoints exist (`backend/api/websocket/`). All three share a single `WebSocketManager`: broadcasts go to **every connected client regardless of which channel was joined**, so clients should dispatch on the message `type` field. All channels are server-push only — incoming client frames are read solely to detect disconnects (the frontend sends `ping` frames for its own stale-connection detection; there is no server command protocol).

Message envelope:

```json
{ "type": "<message_type>", "data": { ... } }
```

| Channel | Message types | Payload built from |
|---------|---------------|--------------------|
| `/ws/dashboard` | `dashboard_snapshot` | `DashboardSnapshot` (`backend/dashboard/schemas/dashboard_payload.py`): timestamp, fleet totals, fleet health score, attention count, and per-vehicle `VehicleDashboardSummary` rows (operational status, live telemetry values, subsystem health scores/statuses, driver scores/risk, active alert info, event flags, trip/route context) |
| `/ws/trips` | `trips_snapshot` | `TripsSnapshot` (`backend/trips/schemas/trip_payload.py`): timestamp, trip list (per-trip metrics, event counts, severity, live-only fields), totals |
| `/ws/alerts` | `alert_event` | Alert lifecycle events (`alert_created`, `alert_acknowledged`, `alert_resolved`) keyed by vehicle-scoped `alert_id` so clients can reconcile against REST rows |

Publishers feed each worker via `asyncio.Queue`; workers drain their queue and call `WebSocketManager.broadcast()`. See `docs/API.md` for concrete payload examples matching these schemas.

## Design Decisions

**Why async SQLAlchemy?**
- Fleet simulation and WebSocket broadcasting run concurrently with database I/O; `asyncpg` avoids blocking the event loop during persistence.

**Why a simulator instead of real OBD-II hardware?**
- DriveVitals is a simulated fleet platform; no hardware integration is implemented. The telemetry schema is deliberately OBD-II-shaped so a real source could replace the generator without changing anything downstream of `TelemetryPipeline`.

**Why rule-based analytics (no ML)?**
- Rule-based engines are deterministic, auditable, and traceable to named thresholds. Machine learning is an explicit non-goal of the current implementation (see root README roadmap).

**Why split WebSocket channels?**
- Dashboard, trips, and alerts originate from different publishers and cadences; separate queues isolate slow consumers of one stream from another. Note the shared manager means delivery is currently fan-out to all clients; channel separation is about production cadence, not access control.

## Limitations

- **No production deployment**: single process, in-memory runtime state; no horizontal scaling, load balancing, or caching layer.
- **Simulated data only**: no real OBD-II/CAN hardware; all vehicle data comes from `OBDGenerator`.
- **No authentication/authorization**: all endpoints (REST and WebSocket) are public; no RBAC or audit logging.
- **No machine learning**: all analytics and maintenance estimates are rule-based heuristics.
- **Single fleet per runtime**: one in-memory fleet; no multi-tenant isolation.
- **Shared WebSocket broadcast**: messages are delivered to all connected clients; there is no per-client filtering.

See `docs/LIMITATIONS.md` for full scope and future work.
