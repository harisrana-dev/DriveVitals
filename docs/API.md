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

All REST routes are versioned under `/api/v1` and are **read-oriented** with two mutation endpoints in the alerts router. Responses are wrapped in a standard envelope:

```json
{
  "data": ...,
  "count": ...      // present on paginated list responses
}
```

### 2.1 Pagination & Filtering

- `limit` — maximum records to return (default `100`, range `1..500`).
- `offset` — records to skip (default `0`).
- Filters are passed as query parameters where documented below.

### 2.2 Endpoints

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

#### Alerts

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/v1/alerts` | List alerts. Filters: `severity`, `type`, `acknowledged`. |
| `GET` | `/api/v1/alerts/{vehicle_id}` | List alerts for a vehicle. Same filters. |
| `POST` | `/api/v1/alerts/{alert_id}/acknowledge` | Mark an alert as acknowledged. |
| `POST` | `/api/v1/alerts/{alert_id}/resolve` | Mark an alert as resolved. |

#### System

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/v1/system/health` | Health check (includes DB connectivity). |
| `GET` | `/api/v1/system/version` | Application and API version. |
| `GET` | `/api/v1/system/status` | Operational status with uptime. |

#### Root

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/` | Static status payload: `{"name": "DriveVitals", "status": "running"}`. |

---

## 3. WebSocket API

DriveVitals exposes two unauthenticated WebSocket endpoints. Both are **server-push only**: the backend broadcasts snapshots; client-to-server messages are read only to detect disconnects.

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

### 3.3 Reconnect Behavior

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
| `throttle_position_percent` | % | 0–100 |
| `brake_pressure` | 0.0–1.0 | Internal representation; persisted as `brake_percent` (0–100). |
| `coolant_temperature_c` | °C | |
| `engine_load_percent` | % | 0–100 |
| `fuel_rate_lph` | L/h | |
| `fuel_level_percent` | % | 0–100 |
| `odometer_km` | km | Lifetime vehicle odometer. |

---

## 5. Error Behavior

- **404** — entity not found (e.g. vehicle, trip, driver).
- **400** — validation failure (e.g. `limit` outside `1..500`, negative `offset`).
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
