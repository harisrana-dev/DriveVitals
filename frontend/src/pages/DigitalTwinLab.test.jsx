import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderToString } from 'react-dom/server';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { AuthContext } from '../context/authCtx';
import { DigitalTwinLabPage } from './DigitalTwinLab';
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
