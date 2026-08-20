# DriveVitals Backend

This document covers the DriveVitals backend architecture, setup, and development workflow.

## Stack

- **Language**: Python 3.12+
- **Framework**: FastAPI (async HTTP server)
- **Database**: PostgreSQL 16 (persistent vehicle/driver/fleet state)
- **ORM**: SQLAlchemy 2.x with async support (asyncpg driver)
- **Migrations**: Alembic (schema versioning)
- **WebSockets**: native FastAPI WebSocket support
- **Simulation**: in-process OBD-II telemetry generator (Ornstein-Uhlenbeck noise model)
- **Testing**: pytest (unit + integration + API tests)

## Architecture Overview

The backend follows a layered, responsibility-driven structure:

```
backend/
├── api/                       # REST + WebSocket endpoints
│   ├── v1/
│   │   ├── routers/          # Individual route modules
│   │   │   ├── analytics.py
│   │   │   ├── drivers.py
│   │   │   ├── vehicles.py
│   │   │   ├── fleet.py
│   │   │   ├── trips.py
│   │   │   ├── maintenance.py
│   │   │   ├── alerts.py
│   │   │   └── websocket.py   # WebSocket handlers
│   │   └── dependencies.py   # FastAPI dependency injection
│   └── models/               # Pydantic request/response schemas
│
├── application/              # Core business logic layer
│   ├── runtime.py           # DriveVitalsRuntime - singleton app manager
│   ├── fleet_runner.py      # Per-vehicle simulation & trip execution
│   ├── telemetry_pipeline.py # Stream processing (OBD raw → normalized)
│   ├── persistence.py        # DB persist operations for trips/analytics
│   ├── analytics/            # Rule-based analysis engines
│   │   ├── trip_intelligence.py
│   │   ├── vehicle_health_analyzer.py
│   │   ├── maintenance_analyzer.py
│   │   ├── driver_analytics.py
│   │   └── alert_generator.py
│   ├── driver_statistics_reconciler.py # Async job for daily reconciliation
│   └── models/               # Business domain models (Vehicle, Trip, Driver, etc.)
│
├── db/                       # Database persistence layer
│   ├── session.py           # SQLAlchemy engine + sessionmaker (async)
│   ├── models.py            # SQLAlchemy ORM classes
│   └── migrations/          # Alembic migration scripts
│
├── telemetry/                # Simulation & telemetry generation
│   ├── generators/          # OBD-II data generators
│   │   ├── base.py         # Abstract generator interface
│   │   └── obd_generator.py # Ornstein-Uhlenbeck stochastic process
│   └── models.py            # Telemetry data classes

├── telemetry_sink.py         # WebSocket publisher (broadcasts dashboards + trip snapshots)
├── conftest.py              # Test fixtures and configuration
└── main.py                  # Entry point: create app, start runtime
```

## Key Responsibilities

**DriveVitalsRuntime**
- Central orchestrator; holds application state
- Manages live vehicle simulations (FleetRunner instances)
- Exposes methods to: start/stop vehicles, fetch snapshots, publish WebSocket messages
- Single-process, in-memory, with async-safe persistence to PostgreSQL

**TelemetryPipeline**
- Per-vehicle processor
- Consumes OBD-II values (speed, RPM, throttle, fault codes, etc.)
- Normalizes and filters raw telemetry
- Feeds analytics engines (health, maintenance, trip intelligence)

**Analytics Engines**
- **Trip Intelligence**: detects events (acceleration, hard braking, cornering), computes efficiency metrics
- **Vehicle Health Analyzer**: monitors sensor data, flags degradation, predicts maintenance
- **Driver Analytics**: scores based on safe driving (speeding, harsh maneuvers, fuel efficiency)
- **Maintenance Analyzer**: tracks component wear using OBD-II data, schedules service
- **Alert Generator**: produces alerts for anomalies, thresholds, and maintenance events

All engines work on live telemetry streams. No machine learning; analysis is rule-based.

**Persistence Layer**
- Async SQLAlchemy session; asyncpg for fast PostgreSQL connectivity
- Models: Vehicle, Driver, Fleet, Trip, TelemetrySnapshot, Alert, MaintenanceRecord, etc.
- Alembic manages schema versioning across deployments

**WebSocket Channels**
1. `/ws/dashboard` – Broadcasts fleet-wide snapshots on every engine tick (~10 Hz)
   - Payload: current vehicle positions, speeds, fuel, health, alerts
   - Format: `dashboard_snapshot` (JSON)
   
2. `/ws/trips` – On-demand trip updates when trips complete or progress
   - Payload: trip summary, efficiency, events, driver score
   - Format: `trips_snapshot` (JSON)

## Running Locally

### Prerequisites

- Python 3.12+
- PostgreSQL 16+ running on `localhost:5432` (or configure `POSTGRES_HOST` in `.env`)
- `.env` file with credentials (copy `.env.example` and fill in)

### Setup

```bash
# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run Alembic migrations to initialize schema
cd backend/db/migrations
alembic upgrade head

# Start the backend (from project root)
cd ../..
python -m backend.main
```

The FastAPI server starts on `http://localhost:8000`.

### Configuration

Environment variables (set in `.env`):

- `POSTGRES_USER` – Database user
- `POSTGRES_PASSWORD` – Database password
- `POSTGRES_DB` – Database name (default: `drivevitals_dev`)
- `POSTGRES_HOST` – Database host (default: `localhost`)
- `POSTGRES_PORT` – Database port (default: `5432`)

## Testing

Backend tests are organized by type:

```
tests/
├── unit/                    # Pure logic tests (no DB/network)
│   ├── test_active_trip_snapshot.py
│   ├── test_runtime_resilience.py
│   ├── test_runtime_trip_completion.py
│   └── ... (analytics unit tests)
│
├── integration/             # Multi-layer tests (with DB)
│   ├── test_analytics_pipelines.py
│   └── test_persistence.py
│
└── api/                     # FastAPI endpoint tests (HTTP + WS)
    ├── test_analytics_api.py
    ├── test_driver_api.py
    ├── test_fleet_api.py
    ├── test_trips_api.py
    ├── test_vehicle_api.py
    └── test_websocket.py
```

### Run Tests

```bash
# Requires .env configured with PostgreSQL credentials
pytest

# Run only unit tests (no DB required)
pytest tests/unit

# Run specific test file
pytest tests/unit/test_active_trip_snapshot.py -v

# Run with coverage
pytest --cov=backend tests/
```

### Test Database

Integration and API tests require a live PostgreSQL connection. Tests use the same `.env` credentials.
Database state is cleaned between test runs (fixtures handle setup/teardown).

## API Endpoints

Key REST endpoints implemented:

- `GET /api/v1/fleet` – List all vehicles
- `POST /api/v1/fleet/{vehicle_id}/start` – Start vehicle simulation
- `POST /api/v1/fleet/{vehicle_id}/stop` – Stop vehicle simulation
- `GET /api/v1/fleet/{vehicle_id}/trips` – Get trip history for vehicle
- `GET /api/v1/trips/{trip_id}` – Get trip details
- `GET /api/v1/vehicles` – List vehicles with status
- `GET /api/v1/drivers` – List drivers with stats
- `GET /api/v1/analytics/dashboard` – Current fleet snapshot
- `GET /api/v1/alerts` – Active alerts
- `GET /api/v1/maintenance` – Maintenance records

See `docs/API.md` for full endpoint specification.

### WebSocket Channels

Both channels are established from the frontend:

```javascript
// Fleet-wide snapshot stream
const dashWS = new WebSocket('ws://localhost:8000/ws/dashboard');
dashWS.onmessage = (event) => {
  const { dashboard_snapshot } = JSON.parse(event.data);
  // { vehicles: [...], alerts: [...], fleet_health: ... }
};

// Trip event stream
const tripWS = new WebSocket('ws://localhost:8000/ws/trips');
tripWS.onmessage = (event) => {
  const { trips_snapshot } = JSON.parse(event.data);
  // { completed_trip_id, summary: {...}, events: [...] }
};
```

See `docs/API.md` for full message format.

## Design Decisions

**Why Async SQLAlchemy?**
- WebSocket connections and fleet simulation run concurrent with database I/O
- asyncpg provides low-latency PostgreSQL access without blocking the event loop
- In-memory OBD simulation can proceed while persistence happens in parallel

**Why In-Process OBD Generator (Not Real Hardware)?**
- DriveVitals is a *simulated* fleet platform for portfolio/learning
- Ornstein-Uhlenbeck noise model produces realistic vehicle dynamics
- Enables testing at scale without hardware; no production deployment assumed
- See `docs/telemetry_design.md` for noise model details

**Why Rule-Based Analytics (No ML)?**
- Machine learning was deferred to later implementation phases
- Rule-based engines are deterministic, auditable, and fast
- Each analytics engine (trip intelligence, vehicle health, driver scoring) is extensible
- See `docs/analytics_design.md` for rule specifications

**Why WebSocket Channels Split?**
- `/ws/dashboard` broadcasts system-wide state every tick (high frequency, fan-out to many clients)
- `/ws/trips` sends trip updates asynchronously (event-driven, lower volume)
- Separation prevents dashboard lag from heavy trip processing

**Why SQLAlchemy ORM (Not Raw SQL)?**
- Type safety and IDE autocomplete on model attributes
- Automatic migration tracking (Alembic) for schema versioning
- Easier refactoring; queries are structured as Python objects
- Async support (asyncpg) unblocks concurrent request handling

## Limitations

**No Production Deployment**
- Single process; cannot horizontally scale
- WebSocket state held in memory; no session persistence
- No load balancing, caching, or CDN support

**No Real OBD-II Hardware**
- All vehicle data is simulated
- Generators use stochastic processes, not real vehicle CAN bus data

**No Authentication/Authorization**
- All API endpoints are public
- No role-based access control; no audit logging

**No Machine Learning**
- Analytics engines are rule-based
- Predictive features (e.g., maintenance forecasting) use heuristics only

**Single Fleet per Runtime**
- DriveVitalsRuntime holds one fleet in memory
- No multi-tenant support; no per-customer isolation

See `docs/LIMITATIONS.md` for full scope and future work.
