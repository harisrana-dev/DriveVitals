# DriveVitals Frontend

React 18 + Vite single-page application for the DriveVitals fleet telematics platform. This document reflects the actual code under `frontend/src/`.

## Tech Stack

- **React 18** with function components and hooks
- **Vite** for development server and production builds
- **react-router-dom v7** for routing
- **recharts** for charts, **lucide-react** for icons
- **Context API + custom hooks** for state management (no Redux/Zustand)
- **Vitest** for tests, **ESLint** (flat config) for linting

## Directory Structure

```
frontend/src/
├── api/                      # REST client layer
│   ├── apiClient.js          # fetch wrapper: timeouts, envelope unwrap, PayloadError
│   ├── config.js             # API_BASE / WS_BASE from env vars with localhost defaults
│   ├── endpoints.js          # Centralized REST path builders
│   └── errors.js             # ApiError, NetworkError, TimeoutError, PayloadError
│
├── components/               # Organized by product domain
│   ├── alerts/               # Alert command center components (queue, filters,
│   │                         #   history table, KPI strip, risk panels…)
│   ├── analytics/            # Analytics page sections (fleet performance,
│   │                         #   safety, trip/fuel/driver intelligence…)
│   ├── dashboard/            # Dashboard sections (KPI strip, live fleet table,
│   │                         #   top risk vehicles, maintenance pressure…)
│   ├── drivers/              # Driver cards, leaderboard, profile drawer,
│   │                         #   score ring, behaviour timeline…
│   ├── fleet/                # Vehicle grid/cards, fleet summary, vehicle drawer
│   ├── maintenance/          # Maintenance tables, queues, horizon panel…
│   ├── trips/                # Trips table/KPIs/filters, active trips list, drawer
│   ├── vehicleHealth/        # Health cards/matrix/bars, health drawer…
│   ├── layout/               # AppShell, Sidebar, TopBar
│   ├── common/               # AppLoader, ThemeToggle
│   ├── shared/               # PagePlaceholder
│   └── ui/                   # Primitives: ConnectionBadge (+ test), EmptyState,
│                             #   ErrorBoundary, Skeleton, Spinner
│
├── context/                  # Global state providers
│   ├── LiveDataContext.jsx   # WebSocket subscriptions + REST hydration + merging
│   ├── FleetContext.jsx      # Fleet-level UI state
│   ├── TripsContext.jsx      # Trip list/detail UI state
│   ├── TripDrawerContext.jsx # Trip drawer open/close state
│   ├── VehicleDrawerContext.jsx
│   └── (*Ctx.js / use*.js)   # Context objects + accessor hooks for each provider
│
├── hooks/                    # One hook per data domain + UI utilities
│   ├── useFleetData.js       # Merged live fleet view for the dashboard grid
│   ├── useDashboard.js, useTripsData.js, useDrivers.js, useDriverTrips.js
│   ├── useAlerts.js, useMaintenance.js, useVehicleHealth.js, useAnalytics.js
│   ├── useFleetFilters.js, useTripsFilters.js, useVehicleHealthFilters.js
│   └── useTripTelemetry.js, useSmoothValue.js, useTheme.js,
│       useNow.js, useRelativeTime.js
│
├── pages/                    # Route targets (see Routing below)
│   ├── Introductionpage.jsx  # Landing page ("/")
│   ├── login.jsx, signup.jsx # Static demo UI only — no auth backend exists
│   ├── Dashboard.jsx, Fleet.jsx, Trips.jsx, Drivers.jsx, Alerts.jsx,
│   │   Analytics.jsx, VehicleHealth.jsx, Maintenance.jsx, Settings.jsx
│   └── LiveTelemetry.jsx, 404page.jsx   # Present but not currently routed
│
├── services/                 # Domain mapping + typed API modules
│   ├── alertAdapter.js       # Applies /ws/alerts lifecycle events to alert rows
│   ├── driverAdapter.js      # Driver data shaping
│   └── api/                  # alertApi, analyticsApi, driverApi, healthApi,
│                             #   maintenanceApi, telemetryApi, tripApi, vehicleApi
│
├── websocket/                # WebSocket client
│   ├── connectionManager.js  # Per-URL channels: reconnect/backoff/jitter,
│   │                         #   heartbeat, stale detection, pub/sub subscribe
│   └── index.js              # Channel registry: dashboard | trips | alerts
│
├── styles/                   # Global CSS (theme, typography, animations, auth)
├── utils/                    # Pure helpers (formatters, filters, scoring utils;
│                             #   most have co-located .test.js files)
├── App.jsx                   # Router + provider tree
└── main.jsx                  # Entry point
```

## Routing

Defined in `App.jsx`:

| Path | Page component |
|------|----------------|
| `/` | `Introductionpage` (Get Started landing) |
| `/login`, `/signup` | Static demo UI only — no authentication exists |
| `/dashboard` | `Dashboard` |
| `/fleet` | `Fleet` |
| `/trips` | `Trips` |
| `/drivers` | `Drivers` |
| `/alerts` | `Alerts` |
| `/analytics` | `Analytics` |
| `/vehicle-health` | `VehicleHealth` |
| `/maintenance` | `Maintenance` |
| `/settings` | `Settings` |
| `*` | Redirects to `/dashboard` |

Shell routes render inside `components/layout/AppShell`. `LiveTelemetry.jsx` and `404page.jsx` exist but are not currently routed.

Providers wrap the whole tree in this order: `LiveDataProvider → FleetProvider → TripsProvider → TripDrawerProvider`.

## Real-Time Data (WebSocket)

`src/websocket/index.js` registers three channels against the backend:

| Channel | Message type handled |
|---------|---------------------|
| `ws://{WS_BASE}/ws/dashboard` | `dashboard_snapshot` |
| `ws://{WS_BASE}/ws/trips` | `trips_snapshot` |
| `ws://{WS_BASE}/ws/alerts` | `alert_event` |

`connectionManager.js` implements per-channel connection handling:

- Reconnect with exponential backoff (1 s base, 30 s cap) plus jitter
- Heartbeat: sends `{"type":"ping"}` every 30 s; connections stale after 45 s of silence are dropped and reconnected
- Pub/sub API (`subscribeToChannel`) so multiple consumers share one socket per channel
- Connection states: `connecting` / `live` / `offline`

All messages arrive in the backend envelope `{ "type": "<message_type>", "data": { ... } }`. Because the backend broadcasts to every connected client, handlers filter on `type`.

### `/ws/dashboard` payload

The `data` object is the backend's `DashboardSnapshot` (defined in `backend/dashboard/schemas/dashboard_payload.py`). Structurally (subset of fields shown):

```json
{
  "type": "dashboard_snapshot",
  "data": {
    "timestamp": "2026-08-21T12:00:00+00:00",
    "total_fleet": 6,
    "active_vehicle_count": 4,
    "fleet_health_score": 82.5,
    "attention_required": 1,
    "vehicles": [
      {
        "vehicle_id": "V-101",
        "driver_id": "D-101",
        "vehicle_name": "2022 Ford Transit",
        "driver_name": "Alice Smith",
        "operational_status": "ACTIVE",
        "speed_kmh": 45.2,
        "rpm": 2100,
        "throttle_position_percent": 32.5,
        "brake_percent": 0.0,
        "fuel_level_percent": 64.0,
        "coolant_temperature_c": 88.5,
        "engine_load_percent": 45.0,
        "overall_health_score": 87.0,
        "overall_health_status": "good",
        "engine_health": 90.0,
        "cooling_health": 88.0,
        "brake_health": 85.0,
        "transmission_health": 89.0,
        "fuel_system_health": 86.0,
        "driver_safety_score": 92.0,
        "driver_risk_level": "low",
        "active_alert_count": 0,
        "active_alert_text": null,
        "active_event_types": ["speeding"],
        "speeding": true,
        "aggressive_throttle": false,
        "harsh_braking": false,
        "high_rpm": false,
        "odometer_km": 45230.5,
        "last_updated_at": "2026-08-21T12:00:00+00:00",
        "trip_status": "active",
        "route_id": "R-101",
        "route_name": "Downtown Loop"
      }
    ]
  }
}
```

Field values are illustrative; the field names and structure match `VehicleDashboardSummary`. See `docs/API.md` for full payload references.

### `/ws/trips` payload

The `data` object is the backend's `TripsSnapshot` (`backend/trips/schemas/trip_payload.py`): timestamp, per-trip rows (metrics, behaviour event counts, severity, safety score/grade, live-only speed/flag fields), and totals. Active-trip updates arrive once per tick; completed-trip sets are broadcast when trips finish.

### `/ws/alerts` payload

`alert_event` messages carry alert lifecycle events (`alert_created`, `alert_acknowledged`, `alert_resolved`), applied to the local alert list via `services/alertAdapter.js`.

## State Management (`LiveDataContext`)

`context/LiveDataContext.jsx` is the central data hub:

- Subscribes to all three WebSocket channels and exposes per-channel connection state
- Hydrates initial data over REST (`listVehicles`, `listDrivers`, `listDriverStatistics`, `listVehicleHealth`, `getHealthConfig`, `listMaintenance`, `listAlerts`, `listTelemetry`, `listTrips`)
- Merges live snapshots with REST data (e.g. `buildFleetVehicles` joins vehicles, health, drivers, and live dashboard rows; `mergeTripsPayload` de-duplicates trips by id)
- Exposes mutations: alert acknowledge/resolve, maintenance completion, re-sync

Domain hooks (`useFleetData`, `useTripsData`, `useAlerts`, …) read from this context and shape data for their pages.

## REST Integration

- `api/config.js` reads `VITE_API_BASE` (default `http://localhost:8000/api/v1`) and `VITE_WS_BASE` (default `ws://localhost:8000`)
- `apiClient.js` wraps `fetch` with a 15 s timeout and unwraps the backend response envelope; failures raise typed errors from `errors.js`
- `endpoints.js` centralizes path construction; `services/api/*Api.js` modules group calls by domain

Note: some paths declared in `endpoints.js` are not yet fully aligned with the backend router layout (documented in the root README roadmap); the modules above reflect what the frontend actually calls today.

## Development

### Prerequisites

- Node.js 22 and npm (CI uses Node 22)
- Backend running on `http://localhost:8000` (see `backend/README.md`)

### Commands

```bash
npm ci            # clean install from package-lock.json (CI uses this)
npm install       # regular install
npm run dev       # dev server on http://localhost:5173
npm test          # run all Vitest tests once (vitest run)
npm test -- src/utils/alerts.test.js   # run a specific file
npx vitest        # watch mode
npm run lint      # ESLint (flat config, eslint.config.js)
npm run build     # production build to dist/
npx vite preview  # serve the production build locally
```

### Environment Variables

Optional `.env` in `frontend/`:

```
VITE_API_BASE=http://localhost:8000/api/v1
VITE_WS_BASE=ws://localhost:8000
```

Defaults point at a local backend; overrides are read at build/dev time via Vite.

## Testing

Tests run with **Vitest** (`vitest.config.js`). Current test files:

- `components/ui/ConnectionBadge.test.jsx`
- `services/alertAdapter.test.js`
- `services/driverAdapter.test.js`
- `services/api/analyticsApi.test.js`
- `utils/alerts.test.js`
- `utils/dashboard.test.js`
- `utils/driverBenchmark.test.js`
- `utils/driverInsights.test.js`
- `utils/driverTrend.test.js`
- `utils/maintenance.test.js`

CI (`.github/workflows/ci.yml`) runs `npm ci`, `npm test`, and `npm run lint` on Node 22.
