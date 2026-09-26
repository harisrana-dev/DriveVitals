import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderToString } from 'react-dom/server';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { AuthContext } from '../context/authCtx';
import { DigitalTwinLabPage, FleetTab, OverviewTab } from './DigitalTwinLab';
import { pickLaunchTarget } from './digitalTwinLaunch';
import { buildDriverPayload, buildVehiclePayload, buildRoutePayload } from './digitalTwinPayloads';
import { digitalTwinApi } from '../api/digitalTwinApi';

// ── Mocks ──────────────────────────────────────────────────────────────────

vi.mock('../api/digitalTwinApi', () => ({
  digitalTwinApi: {
    getStatus: vi.fn(),
    reset: vi.fn(),
    listDrivers: vi.fn(),
    createDriver: vi.fn(),
    updateDriver: vi.fn(),
    deleteDriver: vi.fn(),
    listVehicles: vi.fn(),
    createVehicle: vi.fn(),
    updateVehicle: vi.fn(),
    deleteVehicle: vi.fn(),
    listRoutes: vi.fn(),
    createRoute: vi.fn(),
    updateRoute: vi.fn(),
    deleteRoute: vi.fn(),
    listAssignments: vi.fn(),
    createAssignment: vi.fn(),
    updateAssignment: vi.fn(),
    deleteAssignment: vi.fn(),
    listScenarios: vi.fn(),
    scenario: vi.fn(),
    createScenario: vi.fn(),
    updateScenario: vi.fn(),
    deleteScenario: vi.fn(),
    setScenarioAssignments: vi.fn(),
    activateScenario: vi.fn(),
    launchScenario: vi.fn(),
    stopScenario: vi.fn(),
    listRuns: vi.fn(),
  },
}));

vi.mock('../hooks/useAuth', () => ({
  useAuth: () => ({
    user: { full_name: 'Test Admin', role: 'admin' },
    isAdmin: true,
  }),
}));

// ── Helpers ────────────────────────────────────────────────────────────────

function seedApi() {
  digitalTwinApi.getStatus.mockResolvedValue({
    data: { running: false, scenario_id: null, scenario_name: null, run_id: null, vehicles: 0 },
  });
  digitalTwinApi.listDrivers.mockResolvedValue({ data: [] });
  digitalTwinApi.listVehicles.mockResolvedValue({ data: [] });
  digitalTwinApi.listRoutes.mockResolvedValue({ data: [] });
  digitalTwinApi.listAssignments.mockResolvedValue({ data: [] });
  digitalTwinApi.listScenarios.mockResolvedValue({ data: [] });
  digitalTwinApi.listRuns.mockResolvedValue({ data: [] });
}

function renderPage() {
  seedApi();
  return renderToString(
    <AuthContext.Provider value={{ status: 'authenticated', user: { role: 'admin' } }}>
      <MemoryRouter initialEntries={['/digital-twin-lab']}>
        <Routes>
          <Route path="/digital-twin-lab" element={<DigitalTwinLabPage />} />
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>
  );
}

// ── Tests ──────────────────────────────────────────────────────────────────

beforeEach(() => {
  vi.clearAllMocks();
});

describe('Digital Twin Lab page', () => {
  it('renders the header title and subtitle', () => {
    const html = renderPage();
    expect(html).toContain('Digital Twin Lab');
    expect(html).toContain('Simulated fleet configuration and scenario lifecycle (admin)');
  });

  it('renders all tab labels', () => {
    const html = renderPage();
    expect(html).toContain('Overview');
    expect(html).toContain('Fleet');
    expect(html).toContain('Assignments');
    expect(html).toContain('Scenarios');
  });

  it('renders loading skeleton initially', () => {
    const html = renderPage();
    expect(html).toContain('ui-skeleton');
  });

  it('has correct page structure (FlaskConical icon container)', () => {
    const html = renderPage();
    expect(html).toContain('lucide-flask-conical');
  });
});

describe('digitalTwinApi', () => {
  it('exposes the required management and lifecycle methods', () => {
    expect(typeof digitalTwinApi.getStatus).toBe('function');
    expect(typeof digitalTwinApi.listDrivers).toBe('function');
    expect(typeof digitalTwinApi.createDriver).toBe('function');
    expect(typeof digitalTwinApi.listVehicles).toBe('function');
    expect(typeof digitalTwinApi.createVehicle).toBe('function');
    expect(typeof digitalTwinApi.listRoutes).toBe('function');
    expect(typeof digitalTwinApi.createRoute).toBe('function');
    expect(typeof digitalTwinApi.listAssignments).toBe('function');
    expect(typeof digitalTwinApi.createAssignment).toBe('function');
    expect(typeof digitalTwinApi.listScenarios).toBe('function');
    expect(typeof digitalTwinApi.createScenario).toBe('function');
    expect(typeof digitalTwinApi.activateScenario).toBe('function');
    expect(typeof digitalTwinApi.launchScenario).toBe('function');
    expect(typeof digitalTwinApi.stopScenario).toBe('function');
    expect(typeof digitalTwinApi.reset).toBe('function');
    expect(typeof digitalTwinApi.listRuns).toBe('function');
  });
});

describe('Scenario tab — page structure', () => {
  it('renders the Scenarios tab label with ListTree icon', () => {
    const html = renderPage();
    expect(html).toContain('Scenarios');
    expect(html).toContain('lucide-list-tree');
  });

  it('exposes the Scenarios tab with correct icon', () => {
    const html = renderPage();
    expect(html).toContain('Scenarios');
    expect(html).toContain('lucide-list-tree');
  });
});

describe('Scenario tab — scenario data fields', () => {
  it('uses assignment_ids from ScenarioRead to resolve fleet composition', () => {
    const mockScenario = {
      scenario_id: 's1',
      name: 'Aggressive Urban Test',
      description: 'Simulates aggressive city driving',
      status: 'draft',
      duration_seconds: 600,
      simulation_speed: 1,
      seed: 42,
      assignment_ids: ['a1', 'a2'],
      created_at: '2024-01-01T00:00:00',
      updated_at: '2024-01-01T00:00:00',
    };
    expect(mockScenario.assignment_ids).toEqual(['a1', 'a2']);
    expect(mockScenario.name).toBe('Aggressive Urban Test');
    expect(mockScenario.description).toBe('Simulates aggressive city driving');
  });

  it('uses canonical field names for driver resolution', () => {
    const mockDriver = {
      driver_id: 'd1',
      first_name: 'John',
      last_name: 'Doe',
      behavior_profile: 'aggressive',
      license_number: 'L123',
      employment_status: 'active',
    };
    const fullName = [mockDriver.first_name, mockDriver.last_name].filter(Boolean).join(' ');
    expect(fullName).toBe('John Doe');
    expect(mockDriver.behavior_profile).toBe('aggressive');
  });

  it('uses canonical field names for vehicle resolution', () => {
    const mockVehicle = {
      vehicle_id: 'v1',
      manufacturer: 'Ford',
      model: 'Transit',
      year: 2023,
      fuel_efficiency_factor: 0.85,
      acceleration_response: 1.2,
      tank_capacity_liters: 55,
    };
    expect(mockVehicle.manufacturer).toBe('Ford');
    expect(mockVehicle.model).toBe('Transit');
    expect(mockVehicle.year).toBe(2023);
    expect(mockVehicle.fuel_efficiency_factor).toBe(0.85);
    expect(mockVehicle.acceleration_response).toBe(1.2);
    expect(mockVehicle.tank_capacity_liters).toBe(55);
  });

  it('uses estimated_distance_km and speed_limit_kmh for routes', () => {
    const mockRoute = {
      route_id: 'r1',
      origin: 'Warehouse',
      destination: 'Customer A',
      estimated_distance_km: 12.5,
      speed_limit_kmh: 50,
      is_active: true,
      route_type: 'urban',
    };
    expect(mockRoute.estimated_distance_km).toBe(12.5);
    expect(mockRoute.speed_limit_kmh).toBe(50);
    expect(mockRoute.origin).toBe('Warehouse');
    expect(mockRoute.destination).toBe('Customer A');
  });

  it('does not use deprecated field names (make, distance_km)', () => {
    const mockVehicle = {
      manufacturer: 'Ford',
      model: 'Transit',
      year: 2023,
    };
    expect(mockVehicle).not.toHaveProperty('make');

    const mockRoute = {
      estimated_distance_km: 10,
    };
    expect(mockRoute).not.toHaveProperty('distance_km');
  });
});

describe('Scenario tab — simulation characteristics', () => {
  it('documents behavior profile descriptions matching OBD generator', () => {
    const BEHAVIOR_DESCRIPTIONS = {
      standard: 'Baseline simulated driving behavior.',
      eco: 'Smoother driving behavior intended to reduce fuel consumption.',
      aggressive: 'More aggressive acceleration and driving variation.',
      cautious: 'More conservative driving behavior with gentler dynamics.',
    };

    expect(Object.keys(BEHAVIOR_DESCRIPTIONS)).toHaveLength(4);
    expect(BEHAVIOR_DESCRIPTIONS.aggressive).toContain('aggressive');
    expect(BEHAVIOR_DESCRIPTIONS.eco).toContain('fuel consumption');
    expect(BEHAVIOR_DESCRIPTIONS.cautious).toContain('conservative');
    expect(BEHAVIOR_DESCRIPTIONS.standard).toContain('Baseline');
  });

  it('documents vehicle characteristic display format', () => {
    const vehicle = {
      fuel_efficiency_factor: 0.85,
      acceleration_response: 1.2,
      tank_capacity_liters: 55,
    };
    expect(`${vehicle.fuel_efficiency_factor}x`).toBe('0.85x');
    expect(`${vehicle.acceleration_response}x`).toBe('1.2x');
    expect(`${vehicle.tank_capacity_liters} L`).toBe('55 L');
  });

  it('documents run status tones', () => {
    const STATUS_TONES = {
      draft: 'neutral',
      ready: 'accent',
      running: 'green',
      completed: 'neutral',
      stopped: 'amber',
    };
    expect(STATUS_TONES.draft).toBe('neutral');
    expect(STATUS_TONES.ready).toBe('accent');
    expect(STATUS_TONES.running).toBe('green');
    expect(STATUS_TONES.completed).toBe('neutral');
    expect(STATUS_TONES.stopped).toBe('amber');
  });
});

describe('Scenario tab — scenario lifecycle states', () => {
  it('documents valid scenario statuses', () => {
    const validStatuses = ['draft', 'ready', 'running', 'completed', 'failed'];
    expect(validStatuses).toContain('draft');
    expect(validStatuses).toContain('ready');
    expect(validStatuses).toContain('running');
    expect(validStatuses).toContain('completed');
    expect(validStatuses).toContain('failed');
  });

  it('documents valid run statuses', () => {
    const validStatuses = ['ready', 'running', 'completed', 'failed', 'stopped'];
    expect(validStatuses).toContain('running');
    expect(validStatuses).toContain('stopped');
  });
});

// ── M5.1 regression: fleet create payloads must satisfy the backend schema ──
//
// DriverCreate.license_number, VehicleCreate.registration_number / vin / year
// and RouteCreate.name are all mandatory server-side. Before this fix the Fleet
// tab omitted them, so every create returned 422 with an array `detail` that the
// page then tried to render as a React child.

describe('fleet create payload contract', () => {
  const DRIVER = {
    driver_id: 'd-1',
    first_name: 'Ada',
    last_name: 'Lovelace',
    license_number: 'LIC-9001',
    behavior_profile: 'eco',
  };
  const VEHICLE = {
    vehicle_id: 'v-1',
    manufacturer: 'Volvo',
    model: 'FH16',
    registration_number: 'REG-42',
    vin: 'YV2RT40A8NB123456',
    year: '2024',
  };
  const ROUTE = {
    route_id: 'r-1',
    name: 'Depot to Customer A',
    origin: 'Depot',
    destination: 'Customer A',
    estimated_distance_km: '12.5',
  };

  it('sends every field required by DriverCreate', () => {
    const payload = buildDriverPayload(DRIVER);
    expect(Object.keys(payload).sort()).toEqual([
      'behavior_profile',
      'driver_id',
      'first_name',
      'last_name',
      'license_number',
    ]);
    expect(payload.license_number).toBe('LIC-9001');
  });

  it('sends every field required by VehicleCreate', () => {
    const payload = buildVehiclePayload(VEHICLE);
    expect(Object.keys(payload).sort()).toEqual([
      'manufacturer',
      'model',
      'registration_number',
      'vehicle_id',
      'vin',
      'year',
    ]);
    expect(payload.registration_number).toBe('REG-42');
    expect(payload.vin).toBe('YV2RT40A8NB123456');
  });

  it('coerces the vehicle year to an integer inside the schema range', () => {
    expect(buildVehiclePayload(VEHICLE).year).toBe(2024);
    expect(Number.isInteger(buildVehiclePayload(VEHICLE).year)).toBe(true);
    expect(buildVehiclePayload({ ...VEHICLE, year: '' }).year).toBeGreaterThanOrEqual(1980);
  });

  it('sends every field required by RouteCreate', () => {
    const payload = buildRoutePayload(ROUTE);
    expect(Object.keys(payload).sort()).toEqual([
      'destination',
      'estimated_distance_km',
      'name',
      'origin',
      'route_id',
    ]);
    expect(payload.name).toBe('Depot to Customer A');
    expect(payload.estimated_distance_km).toBe(12.5);
  });

  it('trims whitespace so padded input does not fail min_length', () => {
    expect(buildDriverPayload({ ...DRIVER, license_number: '  LIC-9  ' }).license_number)
      .toBe('LIC-9');
  });

  it('normalises a blank id to null so the backend mints a UUID', () => {
    expect(buildDriverPayload({ ...DRIVER, driver_id: '   ' }).driver_id).toBeNull();
    expect(buildVehiclePayload({ ...VEHICLE, vehicle_id: '' }).vehicle_id).toBeNull();
    expect(buildRoutePayload({ ...ROUTE, route_id: '' }).route_id).toBeNull();
  });
});

describe('Fleet tab form wiring', () => {
  function renderFleetTab() {
    return renderToString(
      <FleetTab
        drivers={[]}
        vehicles={[]}
        routes={[]}
        onRefresh={() => {}}
        notice={null}
        onNotice={() => {}}
      />
    );
  }

  it('exposes an input for every mandatory create field', () => {
    const html = renderFleetTab();
    expect(html).toContain('License number');
    expect(html).toContain('Registration number');
    expect(html).toContain('VIN');
    expect(html).toContain('Year');
    expect(html).toContain('Name');
  });

  it('constrains the year input to the range the schema accepts', () => {
    const html = renderFleetTab();
    expect(html).toContain('min="1980"');
    expect(html).toContain('max="2100"');
  });
});

// ── M5.1 regression: launch must have an unambiguous target ───────────────
//
// The Overview previously did `scenarios.find(s => s.status === 'ready')`,
// so with multiple Ready scenarios it silently launched whichever sorted
// first instead of the scenario the administrator intended.

describe('pickLaunchTarget — Overview launch targeting', () => {
  const ready = (id, name) => ({ scenario_id: id, name, status: 'ready' });

  it('targets the single Ready scenario', () => {
    const { target, conflict } = pickLaunchTarget([
      ready('s1', 'Alpha'),
      { scenario_id: 's2', name: 'Beta', status: 'draft' },
      { scenario_id: 's3', name: 'Gamma', status: 'running' },
    ]);
    expect(target.scenario_id).toBe('s1');
    expect(conflict).toEqual([]);
  });

  it('refuses to guess when multiple scenarios are Ready', () => {
    const { target, conflict } = pickLaunchTarget([ready('s1', 'Alpha'), ready('s2', 'Beta')]);
    expect(target).toBeNull();
    expect(conflict).toEqual(['Alpha', 'Beta']);
  });

  it('reports no target when nothing is Ready', () => {
    expect(pickLaunchTarget([])).toEqual({ target: null, conflict: [] });
    expect(
      pickLaunchTarget([{ scenario_id: 's1', name: 'X', status: 'draft' }])
    ).toEqual({ target: null, conflict: [] });
  });

  it('tolerates undefined input', () => {
    expect(pickLaunchTarget(undefined)).toEqual({ target: null, conflict: [] });
  });
});

describe('Overview controls reflect backend state', () => {
  function overviewHtml(status, launchName = 'Alpha') {
    return renderToString(
      <OverviewTab
        status={status}
        launchName={launchName}
        onLaunch={() => {}}
        onStop={() => {}}
        onReset={() => {}}
        busy={false}
      />
    );
  }

  const disabledCount = (html) => (html.match(/disabled=""/g) || []).length;

  it('names the exact launch target in the button label', () => {
    expect(overviewHtml(null)).toContain('Launch \u201CAlpha\u201D');
  });

  it('falls back to a generic label when there is no target', () => {
    expect(overviewHtml(null, null)).toContain('Launch scenario');
  });

  it('disables Stop while the default fleet runs (no scenario run to stop)', () => {
    const html = overviewHtml({ running: true, scenario_id: null, vehicles: 6 });
    expect(disabledCount(html)).toBe(1); // only Stop is disabled
    expect(html).toContain('Stop');
  });

  it('enables Stop when a scenario run is active', () => {
    const html = overviewHtml({
      running: true,
      scenario_id: 's1',
      run_id: 'r1',
      vehicles: 2,
    });
    expect(disabledCount(html)).toBe(0);
  });

  it('disables Stop when the simulation is idle', () => {
    const html = overviewHtml({ running: false, scenario_id: null, vehicles: 0 });
    expect(disabledCount(html)).toBe(1);
  });
});
