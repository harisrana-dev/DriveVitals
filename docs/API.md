# DriveVitals — REST & WebSocket API Reference

> **Source of truth:** `backend/api/v1/routers/` (REST), `backend/api/websocket/` (WebSocket).
> This document is written from a full read of the implementation, not from old design docs.

---

## 1. Base URL

```
http://localhost:8000
```

Interactive docs (Swagger UI) are available at `http://localhost:8000/docs` when the backend is running.

---

## 2. REST API (`/api/v1`)

All REST routes are versioned under `/api/v1`. The API surface is **read-oriented** for the fleet/analytics domains, with mutations in alerts, trips, maintenance, settings, and the admin-only Digital Twin control plane. Responses are wrapped in a standard envelope:

```json
{
  "data": ...,
  "count": ...      // present on paginated list responses
}
```

### 2.1 Authentication, Roles & Exposure Policy

Authentication uses an opaque bearer session token:

```http
Authorization: Bearer <token>
```

Tokens are revocable; only their SHA-256 hash is stored.

| Role | Capabilities |
|------|--------------|
| `viewer` | Read the fleet, analytics, telemetry, alerts, trips, health and maintenance surface |
| `operator` | Viewer capabilities plus alert acknowledge/resolve, maintenance completion, and trip deletion |
| `admin` | Operator capabilities plus Settings and the whole Digital Twin control plane |

Failure modes: missing/invalid/expired/revoked token → `401`; authenticated but
insufficient role → `403`; inactive user → `401`.

Exposure policy (enforced by `tests/api/test_authorization_perimeter.py`, which
fails if a new route is not explicitly classified):

| Class | Routes | Anonymous result |
|-------|--------|------------------|
| Public credential exchange | `POST /auth/signup`, `POST /auth/login` | allowed |
| Anonymous reads | `/`, `/api/v1/system/health`, `/api/v1/system/version`, `/api/v1/system/status`, and the fleet/analytics read surface (`vehicles`, `drivers`, `routes`, `trips`, `telemetry`, `vehicle-health`, `driver-statistics`, `maintenance`, `alerts`, `analytics`) | `200` — these expose operational data only, never configuration or credentials |
| Session required | `GET /auth/me`, all mutations | `401` |
| Admin required | `/api/v1/settings*`, `/api/v1/digital-twin/*` | `401`/`403` |

WebSocket channels apply the same session check (see §3).

### 2.2 Pagination & Filtering

- `limit` — maximum records to return (default `100`, range `1..500`).
- `offset` — records to skip (default `0`).
- Filters are passed as query parameters where documented below.

### 2.3 Endpoints

74 endpoints across 14 routers. Unless stated otherwise a role of `viewer`,
`operator` or `admin` is sufficient; `[operator]` and `[admin]` mark the
mutations and control-plane reads that require the higher role.

#### Auth

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/api/v1/auth/signup` | Create a user and return a session token. Public. |
| `POST` | `/api/v1/auth/login` | Exchange credentials for a session token. Public. |
| `POST` | `/api/v1/auth/logout` | Revoke the presented session. |
| `GET` | `/api/v1/auth/me` | Current user profile, role, and session expiry. |

#### Vehicles

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/v1/vehicles` | List vehicles. Filters: `status`, `driver`. |
| `GET` | `/api/v1/vehicles/{vehicle_id}` | Get a single vehicle. |

#### Drivers

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/v1/drivers` | List drivers. |
| `GET` | `/api/v1/drivers/{driver_id}` | Get a single driver. |

#### Routes

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/v1/routes` | List routes. |
| `GET` | `/api/v1/routes/{route_id}` | Get a single route. |

#### Trips

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/v1/trips` | List trips. Filters: `vehicle_id`, `driver_id`, `completed` (bool), `status` (comma-separated: `assigned`, `started`, `in_progress`, `completed`, `aborted`), `route_type`. |
| `GET` | `/api/v1/trips/{trip_id}` | Get a single trip. |
| `DELETE` | `/api/v1/trips/{trip_id}` `[operator]` | Delete a trip. |
| `DELETE` | `/api/v1/trips/aborted` `[operator]` | Delete all aborted trips. |

#### Telemetry

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/v1/telemetry` | List telemetry samples across all vehicles. Filters: `latest` (bool — only newest per vehicle), `trip_id`. |
| `GET` | `/api/v1/telemetry/{vehicle_id}` | List telemetry samples for a vehicle. Same filters. |

#### Vehicle Health

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/v1/vehicle-health` | List vehicle health records. |
| `GET` | `/api/v1/vehicle-health/{vehicle_id}` | Get health record for a vehicle. |
| `GET` | `/api/v1/vehicle-health/config` | Health scoring weights and thresholds. |

#### Driver Statistics

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/v1/driver-statistics` | List driver statistics records. |
| `GET` | `/api/v1/driver-statistics/{driver_id}` | Get statistics for a driver. |

#### Maintenance

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/v1/maintenance` | List maintenance records. Filters: `vehicle_id`, `priority`, `component`. |
| `GET` | `/api/v1/maintenance/{vehicle_id}` | List maintenance records for a vehicle. Same filters. |
| `PATCH` | `/api/v1/maintenance/{maintenance_id}/complete` `[operator]` | Mark a maintenance record completed. |

#### Alerts

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/v1/alerts` | List alerts. Filters: `severity`, `type`, `acknowledged`. |
| `GET` | `/api/v1/alerts/stats` | Aggregate alert statistics. Same filters. |
| `GET` | `/api/v1/alerts/{vehicle_id}` | List alerts for a vehicle. Same filters. |
| `POST` | `/api/v1/alerts/{alert_id}/acknowledge` `[operator]` | Mark an alert as acknowledged. |
| `POST` | `/api/v1/alerts/{alert_id}/resolve` `[operator]` | Mark an alert as resolved. |

#### System

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/v1/system/health` | Health check (includes DB connectivity). |
| `GET` | `/api/v1/system/version` | Application and API version. |
| `GET` | `/api/v1/system/status` | Operational status with uptime. |

#### Analytics

Read-only aggregate endpoints (all `GET`):

| Path | Purpose |
|------|---------|
| `/api/v1/analytics/summary` | Fleet-wide KPI summary. |
| `/api/v1/analytics/vehicles` | Per-vehicle analytics rollup. |
| `/api/v1/analytics/drivers` | Per-driver analytics rollup. |
| `/api/v1/analytics/drivers/{driver_id}/trend` | Time series for one driver. |
| `/api/v1/analytics/trips` | Trip-level analytics. |
| `/api/v1/analytics/events` | Behaviour event aggregates. |
| `/api/v1/analytics/events/trend` | Behaviour event trend series. |
| `/api/v1/analytics/fleet-trend` | Fleet-level trend series. |
| `/api/v1/analytics/insights` | Generated operational insights. |
| `/api/v1/analytics/safety-distribution` | Safety score distribution. |

#### Settings

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/v1/settings` `[admin]` | Full settings payload: account, system, and analytics configuration. |
| `GET` | `/api/v1/settings/{category}` `[admin]` | One settings category. The only valid category is `analytics`; anything else is `404`. |
| `PATCH` | `/api/v1/settings/{category}` `[admin]` | Validate and persist a settings update (`analytics`). |

#### Digital Twin (control plane, admin only)

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/v1/digital-twin/status` | Runtime status: running flag, active run, tick configuration. |
| `GET`/`POST`/`PATCH`/`DELETE` | `/api/v1/digital-twin/drivers[/{driver_id}]` | Driver fixtures. |
| `GET`/`POST`/`PATCH`/`DELETE` | `/api/v1/digital-twin/vehicles[/{vehicle_id}]` | Vehicle fixtures. |
| `GET`/`POST`/`PATCH`/`DELETE` | `/api/v1/digital-twin/routes[/{route_id}]` | Route fixtures. |
| `GET`/`POST`/`PATCH`/`DELETE` | `/api/v1/digital-twin/assignments[/{assignment_id}]` | Driver/vehicle/route assignments. |
| `GET`/`POST`/`PATCH`/`DELETE` | `/api/v1/digital-twin/scenarios[/{scenario_id}]` | Scenarios with `seed`, `simulation_speed`, `duration_seconds`. `PATCH` is rejected while the scenario is running. |
| `POST` | `/api/v1/digital-twin/scenarios/{scenario_id}/assignments` | Replace a scenario's assignment set. |
| `POST` | `/api/v1/digital-twin/scenarios/{scenario_id}/activate` | Mark a scenario active. |
| `POST` | `/api/v1/digital-twin/scenarios/{scenario_id}/launch` | Start a run; returns the new `run_id`. |
| `POST` | `/api/v1/digital-twin/scenarios/{scenario_id}/stop` | Stop the active run. |
| `GET` | `/api/v1/digital-twin/scenarios/{scenario_id}/runs` | Persisted run history for a scenario. |
| `POST` | `/api/v1/digital-twin/reset` | Reset control-plane fixtures back to the defaults. |

#### Root

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/` | Static status payload: `{"name": "DriveVitals", "status": "running"}`. |

---

## 3. WebSocket API

DriveVitals exposes three **authenticated** WebSocket endpoints. All are
**server-push only**: the backend broadcasts snapshots; client-to-server messages
are read only to detect disconnects.

Each channel requires the session token as a query parameter, because browsers
cannot set headers on a WebSocket handshake:

```
ws://localhost:8000/ws/dashboard?token=<token>
ws://localhost:8000/ws/trips?token=<token>
ws://localhost:8000/ws/alerts?token=<token>
```

A missing, invalid, expired or revoked token — or an inactive user — closes the
socket during the handshake with code `4401` and reason
`Unauthenticated: missing, invalid or expired session token`. Note that the
check happens **once, at connect time**: revoking a session (logout) does not
close sockets that are already open, it only prevents new connections.

### 3.1 `/ws/dashboard`

Broadcasts fleet-wide dashboard snapshots at the analytics engine tick rate (~1 Hz per active vehicle).

**Message envelope:**

```json
{
  "type": "dashboard_snapshot",
  "data": {
    "timestamp": "2026-08-10T12:00:00+00:00",
    "vehicles": [
      {
        "vehicle_id": "V-101",
        "registration_number": "...",
        "vehicle_name": "2022 Ford Transit",
        "driver_id": "D-101",
        "driver_name": "Alice Smith",
        "operational_status": "ACTIVE",
        "trip_status": "in_progress",
        "odometer_km": 45230.5,
        "overall_health_score": 87,
        "speed_kmh": 45.2,
        "rpm": 2100,
        "throttle_position_percent": 32.5,
        "brake_percent": 0.0,
        "fuel_level_percent": 64.0,
        "coolant_temperature_c": 88.5,
        "engine_load_percent": 45.0,
        "active_alert_count": 0,
        "active_alert_text": null,
        "active_event_types": ["speeding"],
        "speeding": true,
        "aggressive_throttle": false,
        "harsh_braking": false,
        "high_rpm": false,
        "last_updated_at": "2026-08-10T12:00:00+00:00",
        "trip_started_at": "2026-08-10T11:55:00+00:00"
      }
    ]
  }
}
```

**Consumer:** `LiveDataContext` → dashboard vehicle grid, fleet overview, vehicle health cards.

### 3.2 `/ws/trips`

Broadcasts trip snapshots. Two sub-types are emitted on the same channel:

1. **Active-trip updates** — once per tick, containing only currently active (`started` / `in_progress`) trips.
2. **Completion events** — when a trip finishes, the updated completed-trip set is broadcast.

**Message envelope (active trips):**

```json
{
  "type": "trips_snapshot",
  "data": {
    "timestamp": "2026-08-10T12:00:00+00:00",
    "trips": [
      {
        "trip_id": "trip-uuid",
        "status": "in_progress",
        "vehicle_id": "V-101",
        "driver_id": "D-101",
        "vehicle_name": "2022 Ford Transit",
        "driver_name": "Alice Smith",
        "route_id": "R-101",
        "route_type": "urban",
        "route_name": "Downtown → Industrial Park",
        "distance_km": 12.4,
        "duration_seconds": 320.5,
        "average_speed_kmh": 27.8,
        "maximum_speed_kmh": 52.0,
        "fuel_consumed_liters": 0.85,
        "average_fuel_rate_lph": 9.5,
        "safety_score": null,
        "grade": null,
        "started_at": "2026-08-10T11:55:00+00:00",
        "completed_at": null,
        "speeding_event_count": 2,
        "speeding_duration_seconds": 45.0,
        "harsh_braking_count": 0,
        "aggressive_throttle_event_count": 1,
        "aggressive_throttle_duration_seconds": 12.0,
        "high_rpm_event_count": 0,
        "high_rpm_duration_seconds": 0.0,
        "severe_event_count": 0,
        "moderate_event_count": 1,
        "minor_event_count": 2,
        "overall_severity": "moderate",
        "events": [...],
        "current_speed_kmh": 45.2,
        "speeding": true,
        "harsh_braking": false,
        "aggressive_throttle": false,
        "high_rpm": false
      }
    ],
    "total_trips": 1,
    "total_distance_km": 12.4,
    "average_safety_score": 0.0,
    "total_fuel_consumed_liters": 0.85
  }
}
```

**Message envelope (completed trips):**

Same structure, but `status` is `completed` or `aborted`, and completion fields (`safety_score`, `grade`, `completed_at`) are populated.

**Consumer:** `LiveDataContext` → Trips page (`activeTrips`, `historicalTrips`).

### 3.3 `/ws/alerts`

Publishes alert lifecycle events. Every message uses the same envelope with
`"type": "alert_event"`; `data.type` carries the specific transition
(`alert_created`, `alert_acknowledged`, `alert_resolved`). Payloads are keyed by
the vehicle-scoped `alert_id` so the frontend can reconcile them against REST rows.

```json
{
  "type": "alert_event",
  "data": {
    "type": "alert_created",
    "alert_id": "V-101:coolant_high:2026-08-10T12:00:00Z",
    "vehicle_id": "V-101",
    "driver_id": "D-101",
    "trip_id": "trip-uuid",
    "alert_type": "coolant_high",
    "severity": "high",
    "status": "open",
    "acknowledged": false,
    "acknowledged_at": null,
    "created_at": "2026-08-10T12:00:00+00:00",
    "last_triggered_at": "2026-08-10T12:00:00+00:00",
    "resolved_at": null,
    "condition": "coolant_temperature_c > 105",
    "category": "engine",
    "message": "Coolant temperature critical",
    "evidence": {"coolant_temperature_c": 108.2},
    "source": "engine"
  }
}
```

**Consumer:** `LiveDataContext` → Alerts page (feed, severity counters,
acknowledgement state).

### 3.4 Reconnect Behavior

The frontend WebSocket client (`frontend/src/websocket/connectionManager.js`) implements reconnect with exponential backoff plus jitter, and a heartbeat/stale-connection check. The backend does not currently send heartbeats; the client detects stale connections by absence of messages.

### 3.4 Live-vs-Completion Semantics

| Field | Active trip | Completed trip |
|-------|-------------|----------------|
| `safety_score` | `null` (not yet computed) | float (0–100) |
| `grade` | `null` | A/B/C/D/F |
| `completed_at` | `null` | ISO-8601 timestamp |
| `current_speed_kmh` | float | `null` |
| `speeding` / `harsh_braking` / `aggressive_throttle` / `high_rpm` | live flags | `false` |

---

## 4. Telemetry Units

| Field | Unit | Notes |
|-------|------|-------|
| `speed_kmh` | km/h | |
| `rpm` | revolutions/minute | |
| `throttle_percent` | % | 0–100. **REST** `/api/v1/telemetry` field name. |
| `throttle_position_percent` | % | 0–100. **WebSocket** dashboard snapshot field name. |
| `brake_percent` | % | 0–100 on both surfaces. |
| `coolant_temperature_c` | °C | |
| `engine_load_percent` | % | 0–100 |
| `fuel_rate_lph` | L/h | |
| `fuel_level_percent` | % | 0–100 |
| `odometer_km` | km | Lifetime vehicle odometer. |

The in-memory `TelemetrySample` carries `brake_pressure` as 0.0–1.0; it is
converted to the 0–100 `brake_percent` column at persistence time. Live
dashboard fields are nullable and fall back to `0` in the frontend adapters when
a signal is absent.

---

## 5. Error Behavior

- **400** — validation failure (e.g. `limit` outside `1..500`, negative `offset`).
- **401** — missing, invalid, expired or revoked session token (`INVALID_OR_EXPIRED_TOKEN`).
- **403** — authenticated but insufficient role (`INSUFFICIENT_PERMISSIONS`).
- **404** — entity not found (e.g. vehicle, trip, driver).
- **409** — state conflict, e.g. launching while a run is active, editing a
  running scenario, a duplicate assignment triple, or a unique-value collision
  (vehicle VIN/registration, driver licence number).
- **503** — the simulation controller is unavailable (launch/stop/reset).
- **500** — unhandled server error; also returned by `/system/health` when the database is unreachable.

All errors follow the standard FastAPI JSON shape:

```json
{
  "detail": "Vehicle V-999 not found"
}
```

---

## 6. CORS

The backend allows requests from `http://localhost:5173` (the default Vite dev server port). Credentials are not allowed.

---

## 7. Status Semantics

| Term | Meaning |
|------|---------|
| **Active trip** | `status` is `started` or `in_progress`. |
| **Historical trip** | `status` is `completed` or `aborted`. |
| **Stale trip** | An `in_progress` trip row left in the database by a previous runtime session. These are aborted at startup. |

---

## 8. Null Semantics

- `safety_score` and `grade` are `null` for active trips because the score requires the completed trip distance for density normalization.
- `current_speed_kmh` is `null` for completed trips because the vehicle is no longer moving.
- `events` is an empty array `[]` when no behaviour events have been recorded.
