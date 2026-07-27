# Dashboard Frontend Design — DriveVitals

This document defines the contract between the DriveVitals backend and any frontend consuming the live dashboard feed. It describes what the backend guarantees and what the frontend is responsible for; it does not prescribe a specific frontend implementation.

## Connecting to the Backend

The frontend connects to:
```
ws://localhost:8000/ws/dashboard
```
This is a long-lived WebSocket connection, not a request/response API. Once opened, it should be kept open for the lifetime of the dashboard view.

**Backend implementation:** the server accepts the connection, registers it, and pushes JSON messages to it as analytics snapshots are produced (see `docs/design/backend/api_design.md`).

**Frontend responsibility:** open the connection when the dashboard mounts, listen for incoming messages, and close it when the dashboard unmounts.

## Push Model, Not Polling

The backend pushes every `analytics_snapshot` message as soon as it's produced. The frontend should not implement a polling loop (e.g. periodic `fetch`/HTTP requests) to retrieve live dashboard state — there is no REST endpoint for this data, and none is needed. The frontend's job is to listen for incoming JSON messages on the open socket and update state accordingly.

## Message Payload

Every message currently received has this shape:

```json
{
  "type": "analytics_snapshot",
  "vehicle_id": "...",
  "driver_id": "...",
  "trip_id": "...",
  "timestamp": "ISO-8601 string",
  "telemetry": { ... },
  "behaviour": { ... },
  "events": { "completed": [...], "active": [...] }
}
```

`type` is currently always `"analytics_snapshot"`. The frontend can use this field to distinguish message kinds if additional message types are introduced later.

### `telemetry` fields

Raw, point-in-time vehicle readings:

| Field | Meaning |
|---|---|
| `speed_kmh` | Vehicle speed in km/h |
| `rpm` | Engine RPM |
| `engine_load_percent` | Engine load as a percentage |
| `throttle_position_percent` | Throttle position as a percentage |
| `brake_pressure` | Brake pressure reading |
| `coolant_temperature_c` | Coolant temperature in °C |
| `fuel_rate_lph` | Fuel consumption rate in liters/hour |
| `fuel_level_percent` | Fuel tank level as a percentage |
| `odometer_km` | Cumulative odometer reading in km |

### `behaviour` fields

Derived driver-behaviour indicators computed from telemetry:

| Field | Meaning |
|---|---|
| `speeding` | Whether the driver is currently exceeding the applicable speed limit |
| `harsh_braking` | Whether harsh braking is currently detected |
| `aggressive_throttle` | Whether aggressive throttle use is currently detected |
| `high_rpm` | Whether RPM is currently in a high range |
| `speed_excess_kmh` | Amount by which speed currently exceeds the limit, in km/h |
| `severity` | Overall severity classification for current driver behaviour |

### `events` fields

| Field | Meaning |
|---|---|
| `completed` | List of behaviour events that have finished, each with `event_type`, `started_at`, `ended_at`, `duration_seconds`, `distance_km`, and `severity` |
| `active` | List of behaviour event types currently in progress (ongoing, not yet completed) |

## Multiple Vehicles

A single WebSocket connection carries snapshots for all vehicles in the fleet, distinguished by `vehicle_id`. The frontend is responsible for using `vehicle_id` (and `driver_id`/`trip_id` where relevant) to route each incoming snapshot to the correct vehicle's state/UI representation.

## Maintaining Current State (Frontend Responsibility)

Each incoming message represents the latest known state for the given `vehicle_id` at `timestamp`. The frontend is responsible for:

- Keeping a per-vehicle "current snapshot" representation, replaced each time a newer message for that `vehicle_id` arrives.
- Deciding how to accumulate `completed` events over time (e.g. for a history view) versus treating `active` as transient, current-state-only.

This document does not prescribe a specific state-management approach — that is a future frontend decision.

## Reconnect Handling (Conceptual)

If the WebSocket connection drops, the frontend should detect the close/error and attempt to reconnect. Conceptually:

- Detect disconnect (`onclose`/`onerror` equivalent).
- Attempt to re-establish the connection to `ws://localhost:8000/ws/dashboard`.
- Resume listening for `analytics_snapshot` messages once reconnected.

The backend does not currently provide a way to request missed snapshots after a disconnect — a reconnected client simply starts receiving new snapshots as they're produced going forward. Specific retry/backoff strategy is a future frontend decision.

## Summary of Boundaries

| | Owner |
|---|---|
| Opening/closing the WebSocket, listening for messages | Frontend |
| Producing and pushing `analytics_snapshot` messages | Backend |
| Per-vehicle state representation, event history handling | Frontend (future decision) |
| Reconnect/retry strategy | Frontend (future decision) |
| Message shape (`telemetry`, `behaviour`, `events`) | Backend (documented above) |