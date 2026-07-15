# Project Architecture — DriveVitals

## High-Level Overview

DriveVitals ingests raw vehicle telemetry (from a real OBD-II adapter or a simulator), stores it, processes it into meaningful insights, and displays it on a fleet dashboard.

```
┌─────────────────────┐
│  Vehicle / Simulator │
└──────────┬───────────┘
           │
           ▼
┌─────────────────────┐
│ Telemetry Collection │
└──────────┬───────────┘
           │
           ▼
┌─────────────────────┐
│      Database        │
└──────────┬───────────┘
           │
           ▼
┌─────────────────────┐
│  Analytics Engine     │
└──────────┬───────────┘
           │
           ▼
┌─────────────────────┐
│      Dashboard        │
└─────────────────────┘
```

---

## Architectural Layers

### 1. Data Acquisition Layer

Responsible for producing raw telemetry data.

- **OBD-II adapter** — reads live data from a physical vehicle (future/real-world integration)
- **Simulator** — generates physics-inspired synthetic telemetry for development and testing, without needing real hardware

Both sources emit data in the same schema so the rest of the system doesn't need to know or care where the data came from.

### 2. Database Layer

- **PostgreSQL** — primary data store
- **SQLAlchemy** — ORM used to define models and query the database
- **Alembic** — manages schema migrations over time

### 3. Backend Layer

- **FastAPI** — serves REST APIs and handles application logic
- **WebSockets** — stream live telemetry to connected clients in real time
- Organizes logic into routers, services, and models (see `BACKEND_GUIDE.md`)

### 4. Analytics Layer

Turns raw telemetry into actionable intelligence:

- Driver behavior analysis
- Fuel efficiency calculations
- Vehicle health scoring
- Predictive maintenance signals

### 5. Frontend Layer

- **Fleet dashboard** — visualizes KPIs, vehicle status, trip history, and alerts for fleet managers

---

## Project Philosophy

DriveVitals draws a firm line between two categories of data:

| Concept | Meaning |
|---------|---------|
| **Telemetry** | Raw truth — exactly what the vehicle reported, unmodified |
| **Analytics** | Derived intelligence — insights computed *from* telemetry |

This separation matters because:

- Raw telemetry must remain trustworthy and unaltered for auditing, debugging, and re-processing.
- Analytics logic can evolve over time (better models, new metrics) and be recalculated from historical telemetry without losing the original data.

---

## Data Flow

```
Telemetry
   │
   ▼
Analytics Engine
   │
   ▼
Analytics Snapshot
   │
   ▼
Dashboard
```

1. Raw **Telemetry** rows are written as data arrives (from simulator or real adapter).
2. The **Analytics Engine** periodically (or on-demand) processes telemetry into derived metrics.
3. Results are stored as an **AnalyticsSnapshot** — a point-in-time computed summary.
4. The **Dashboard** reads snapshots (not raw telemetry) for fast, pre-computed visualizations.

---

## Why This Architecture

- **Separation of concerns** — each layer has one clear job, making it easier for multiple team members to work in parallel without stepping on each other.
- **Swappable data sources** — the simulator can be replaced by a real OBD-II adapter later without touching the database, backend, or analytics layers.
- **Auditable history** — because telemetry and analytics are separate, you can always recompute analytics differently later without losing the ground truth.