# DriveVitals Frontend

React 18 + Vite web interface for the DriveVitals fleet telematics platform.

## Architecture

**Tech Stack**
- React 18 for UI components and state management
- Vite for fast development and optimized production builds
- Context API for application state (LiveDataContext, FleetContext, TripsContext, etc.)
- Custom hooks for WebSocket and REST integration
- CSS modules and inline styling for component isolation

**Key Directories**
```
frontend/src/
├── pages/              # Top-level page components
│   ├── Dashboard.jsx      # Fleet-wide live view
│   ├── Trips.jsx          # Trip history and analytics
│   ├── Vehicles.jsx       # Vehicle management and status
│   ├── Drivers.jsx        # Driver profiles and statistics
│   ├── Maintenance.jsx    # Maintenance schedules and records
│   ├── Alerts.jsx         # Active and historical alerts
│   ├── Settings.jsx       # Application preferences
│   ├── Login.jsx          # Non-functional auth placeholder
│   ├── Signup.jsx         # Non-functional auth placeholder
│   └── NotFound.jsx       # 404 page
│
├── components/         # Reusable UI components
│   ├── ui/              # Low-level widgets
│   │   ├── ConnectionBadge.jsx
│   │   ├── TelemetryGauge.jsx
│   │   ├── AlertCard.jsx
│   │   ├── Card.jsx
│   │   ├── Button.jsx
│   │   └── ... (10+ shared components)
│   ├── Fleet/           # Fleet-specific components
│   │   ├── VehicleGrid.jsx
│   │   ├── VehicleCard.jsx
│   │   └── FleetHealthSummary.jsx
│   ├── Drawers/         # Slide-out panels for detail views
│   │   ├── TripDrawer.jsx       # Trip detail panel
│   │   ├── VehicleDrawer.jsx    # Vehicle detail panel
│   │   ├── DriverDrawer.jsx     # Driver profile panel
│   │   └── AlertDrawer.jsx      # Alert detail panel
│   └── Modals/          # Dialog components
│       ├── ConfirmDialog.jsx
│       └── ... (other modals)
│
├── contexts/           # Context providers for global state
│   ├── LiveDataContext.jsx    # Real-time dashboard snapshots (/ws/dashboard)
│   ├── FleetContext.jsx       # Fleet configuration and metadata
│   ├── TripsContext.jsx       # Trip history and details (/ws/trips)
│   ├── TripDrawerContext.jsx  # Trip detail drawer state
│   └── VehicleDrawerContext.jsx # Vehicle detail drawer state
│
├── hooks/              # Custom React hooks
│   ├── useWebSocket.js        # WebSocket connection management
│   ├── useDashboard.js        # Dashboard snapshot fetching
│   ├── useTrips.js            # Trip data fetching
│   ├── useVehicles.js         # Vehicle list and status
│   ├── useDrivers.js          # Driver analytics
│   ├── useAlerts.js           # Active alerts
│   ├── useMaintenance.js      # Maintenance records
│   └── useLocalStorage.js     # Persistent user preferences
│
├── services/           # API and WebSocket services
│   ├── api.js         # REST client (analytics, vehicles, drivers, trips, maintenance, alerts)
│   ├── websocket.js   # WebSocket client wrapper
│   └── config.js      # API base URL and configuration
│
├── styles/            # Global CSS
│   ├── index.css      # Reset and layout
│   └── variables.css  # CSS custom properties
│
├── App.jsx            # Root component with routing
├── main.jsx           # Entry point
└── index.html         # Static HTML template
```

## Data Flow

### Live Dashboard (/ws/dashboard)

```
WebSocket /ws/dashboard (backend) 
  ↓ (10 Hz broadcast)
LiveDataContext 
  ↓ (subscribers notified)
Dashboard.jsx, FleetHealthSummary.jsx, etc.
  ↓ (render current state)
Browser UI
```

**Message Format:**
```json
{
  "message_type": "dashboard_snapshot",
  "timestamp": "2024-01-15T10:30:00Z",
  "vehicles": [
    {
      "id": "v001",
      "make": "Tesla",
      "model": "Model 3",
      "status": "active",
      "speed": 45,
      "fuel": 0.85,
      "health": "good",
      "alerts_count": 0
    }
  ],
  "fleet_health": "good",
  "active_trips": 5,
  "total_alerts": 2
}
```

### Trip Events (/ws/trips)

```
Trip completes on backend
  ↓
WebSocket /ws/trips (backend)
  ↓ (event broadcast)
TripsContext 
  ↓ (update trip history)
Trips.jsx, TripDrawer.jsx render new data
  ↓
Browser updates
```

**Message Format:**
```json
{
  "message_type": "trips_snapshot",
  "trip_id": "trip_12345",
  "vehicle_id": "v001",
  "driver_id": "d001",
  "status": "completed",
  "duration_minutes": 25,
  "distance_km": 18.5,
  "fuel_efficiency": 6.2,
  "events": [
    {
      "type": "harsh_acceleration",
      "timestamp": "2024-01-15T10:15:30Z",
      "severity": "medium"
    }
  ],
  "driver_score": 78
}
```

### REST Integration

Pages fetch static or historical data via REST:

```
useVehicles() hook
  ↓
api.getVehicles() 
  ↓ (GET /api/v1/vehicles)
Backend REST endpoint
  ↓ (HTTP response)
Cache in component state
  ↓
Vehicles.jsx renders list
```

**Implemented Endpoints:**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| /api/v1/vehicles | GET | List vehicles with current status |
| /api/v1/fleet | GET | Fleet metadata and summary |
| /api/v1/drivers | GET | Driver profiles and stats |
| /api/v1/trips | GET | Trip history |
| /api/v1/trips/{id} | GET | Trip details |
| /api/v1/alerts | GET | Active alerts |
| /api/v1/analytics/dashboard | GET | Snapshot API (alternative to WebSocket) |
| /api/v1/maintenance | GET | Maintenance records |

See `docs/API.md` for full specification.

## Context Providers

**LiveDataContext**
- Manages `/ws/dashboard` WebSocket connection
- Stores current fleet snapshot
- Exposes: `snapshot`, `isConnected`, `lastUpdate`
- Consumers: Dashboard, cards, status indicators

**FleetContext**
- Fleet metadata (name, vehicle count, location, etc.)
- Persistent across page navigation
- Used by: Fleet management pages

**TripsContext**
- Trip history and details
- Updates from `/ws/trips` WebSocket
- Exposes: `trips`, `selectedTrip`, `selectTrip()`
- Consumers: Trips page, TripDrawer

**TripDrawerContext**
- State for trip detail slide-out panel
- Exposes: `isOpen`, `tripId`, `openDrawer()`, `closeDrawer()`

**VehicleDrawerContext**
- State for vehicle detail slide-out panel
- Exposes: `isOpen`, `vehicleId`, `openDrawer()`, `closeDrawer()`

## Pages

| Page | Purpose | Data Sources | Status |
|------|---------|--------------|--------|
| Dashboard | Fleet-wide live view | /ws/dashboard | Fully implemented |
| Trips | Trip history + analytics | REST + /ws/trips | Fully implemented |
| Vehicles | Vehicle list and detail | REST + /ws/dashboard | Fully implemented |
| Drivers | Driver profiles + scores | REST | Fully implemented |
| Maintenance | Service records + scheduling | REST | Fully implemented |
| Alerts | Active + historical alerts | REST | Fully implemented |
| Settings | User preferences, theme, etc. | localStorage | Partially implemented |
| Login | Demo placeholder (non-functional) | None | Placeholder only |
| Signup | Demo placeholder (non-functional) | None | Placeholder only |

**Note on Login/Signup:** These pages exist as demo UI but authentication is not implemented. The backend has no auth system. All API endpoints are public.

## Development

### Prerequisites

- Node.js 16+ and npm 8+
- Backend running on `http://localhost:8000`

### Setup

```bash
# Install dependencies
npm install

# Start dev server with hot reload
npm run dev

# Build for production
npm run build

# Run tests
npm test

# Run tests in watch mode
npm test -- --watch

# Run linting
npm run lint
```

Dev server runs on `http://localhost:5173`. Open in browser; WebSocket will auto-connect to backend.

### Environment Configuration

Create `.env.local` if needed (optional):

```
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_BASE_URL=ws://localhost:8000
```

Defaults point to `localhost:8000`. For production, update `services/config.js`.

## Testing

Tests are run with Vitest:

```bash
# Run all tests (includes .js and .jsx)
npm test -- --run

# Watch mode
npm test

# Specific test file
npm test -- src/components/ui/ConnectionBadge.test.jsx
```

Test files are co-located:
- `src/components/ui/ConnectionBadge.test.jsx` – Connection badge widget
- `src/hooks/useWebSocket.test.js` – WebSocket hook
- `src/services/api.test.js` – REST client
- `src/contexts/LiveDataContext.test.jsx` – Context provider

## Troubleshooting

**WebSocket connection fails**
- Ensure backend is running on `http://localhost:8000`
- Check browser console for connection errors
- Verify firewall allows WebSocket protocol (ws://)

**API calls return 404**
- Confirm backend is responding: `curl http://localhost:8000/api/v1/vehicles`
- Check that Vite frontend is not making requests to wrong URL
- Review `services/config.js` for API base URL

**CSS or styling issues**
- Clear browser cache and rebuild: `npm run build`
- Restart dev server: Ctrl+C, then `npm run dev`
- Check for conflicting CSS modules

**Tests failing**
- Run `npm test -- --run` to get full output
- Ensure mocks are configured in `vitest.config.js`
- Check that `.jsx` test files are included in test discovery

**Hot reload not working**
- Restart dev server
- Clear `node_modules/.vite` cache
- Ensure file has valid JSX syntax

## Build & Deployment

```bash
# Build optimized production bundle
npm run build

# Output goes to dist/
# Serve locally for testing
npx vite preview
```

The built `dist/` folder contains the static frontend assets. Deploy to:
- AWS S3 + CloudFront
- Vercel / Netlify
- Apache / nginx
- Any static hosting service

**Production Considerations:**
- Update `VITE_API_BASE_URL` environment variable for production backend URL
- Ensure CORS is configured on backend to allow frontend origin
- Use HTTPS for production (ws:// → wss://)
- Consider caching headers on static assets
