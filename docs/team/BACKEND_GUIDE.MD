# Backend Guide — DriveVitals

## Folder Structure

```
backend/
├── api/            # FastAPI routers — HTTP endpoints
├── analytics/       # Analytics computation logic
├── simulator/        # Vehicle telemetry simulators
├── websocket/         # Real-time telemetry streaming
└── services/           # Business logic shared across routers
```

### Responsibilities

| Folder | Responsibility |
|--------|----------------|
| `api/` | Defines HTTP routes, request/response models, input validation. Delegates actual work to `services/`. |
| `analytics/` | Computes driver behavior, fuel efficiency, vehicle health, and predictive maintenance from telemetry. Produces `AnalyticsSnapshot` records. |
| `simulator/` | Generates realistic synthetic OBD-II telemetry for development and testing without real hardware. |
| `websocket/` | Manages WebSocket connections and pushes live telemetry to connected dashboard clients. |
| `services/` | Contains reusable business logic (e.g. trip aggregation, alert generation) called by both `api/` and `websocket/`. |

---

## FastAPI Request Flow

```
Request
   │
   ▼
API Router
   │
   ▼
Service Layer
   │
   ▼
Database
   │
   ▼
Response
```

1. A client sends a request to an endpoint in `api/`.
2. The router validates input (via Pydantic models) and calls the relevant function in `services/`.
3. The service layer contains the actual business logic and talks to the database via SQLAlchemy models.
4. The result is returned back up through the service layer to the router.
5. The router serializes and returns the HTTP response.

**Rule of thumb:** routers should stay thin. If a router function is doing more than validating input and calling a service, that logic belongs in `services/`.

---

## WebSocket Telemetry Flow

```
Simulator / OBD-II Adapter
        │
        ▼
 WebSocket Producer (backend/websocket/)
        │
        ├─────────────► Database (Telemetry table)
        │
        └─────────────► Connected Dashboard Clients (live push)
```

1. The simulator (or real adapter) generates a telemetry reading.
2. The WebSocket producer in `backend/websocket/` receives it.
3. The reading is **persisted** to the `Telemetry` table.
4. The same reading is **broadcast** to any dashboard clients currently connected via WebSocket, so the UI updates in real time without polling.

### Example connection lifecycle

1. Dashboard client opens a WebSocket connection to `/ws/telemetry/{vehicle_id}`.
2. Backend registers the client connection.
3. As new telemetry arrives for that vehicle, it's pushed to the client immediately.
4. On disconnect, the backend cleans up the client registration.

---

## Adding a New Endpoint — Checklist

1. Define request/response schemas (Pydantic) in `api/`
2. Add the route to the appropriate router in `api/`
3. Implement the actual logic in `services/` (not directly in the router)
4. If it touches the database, use existing SQLAlchemy models from `database/models/`
5. Write a test for the new endpoint
6. Update API docs if the behavior is non-obvious