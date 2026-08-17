import { describe, expect, it } from 'vitest';
import {
  computeFleetHealthAverage,
  computeActiveNowCount,
  deriveConnectionState,
  rankVehiclesForTriage,
  summarizeAttention,
  buildMaintenancePressureRows,
  driverRankingQuality,
  SNAPSHOT_STALE_MS,
} from './dashboard';

function vehicle(overrides = {}) {
  return {
    id: 'v-1',
    name: 'V-101',
    driver: 'Ada',
    driverId: 'd-1',
    displayStatus: 'ACTIVE',
    healthScore: 95,
    healthStatus: 'healthy',
    healthCategory: 'healthy',
    lastUpdate: '2026-08-16T10:00:00Z',
    ...overrides,
  };
}

function adaptedAlert(overrides = {}) {
  return {
    alert_id: 'a-1',
    vehicle_id: 'v-1',
    vehicle_name: 'V-101',
    driver_name: null,
    severity: 'medium',
    status: 'active',
    acknowledged: false,
    category: null,
    created_at: '2026-08-16T08:00:00Z',
    ...overrides,
  };
}

function liveEvent(vehicleId, label) {
  return {
    id: `${vehicleId}:${label}`,
    vehicle_id: vehicleId,
    vehicle_name: 'V-101',
    driver_name: null,
    event_type: label.toLowerCase(),
    label,
  };
}

function workItem(overrides = {}) {
  return {
    vehicle_id: 'v-1',
    workKey: 'v-1::oil_change',
    maintenance_type: 'oil_change',
    maintenanceTypeLabel: 'Oil Change',
    dueStatus: 'scheduled',
    remaining_km: 1500,
    priority: 'medium',
    due_date: '2026-09-01T00:00:00Z',
    ...overrides,
  };
}

describe('computeFleetHealthAverage', () => {
  it('returns the rounded mean over vehicles with a real score', () => {
    const vehicles = [
      vehicle({ id: 'a', healthScore: 92 }),
      vehicle({ id: 'b', healthScore: 87 }),
      vehicle({ id: 'c', healthScore: null }),
    ];
    expect(computeFleetHealthAverage(vehicles)).toBe(90);
  });

  it('returns null when no vehicle has a score', () => {
    const vehicles = [vehicle({ id: 'a', healthScore: null }), vehicle({ id: 'b', healthScore: null })];
    expect(computeFleetHealthAverage(vehicles)).toBeNull();
  });

  it('handles empty and non-array input', () => {
    expect(computeFleetHealthAverage([])).toBeNull();
    expect(computeFleetHealthAverage(null)).toBeNull();
  });
});

describe('computeActiveNowCount', () => {
  it('counts vehicles in the ACTIVE display status', () => {
    const vehicles = [
      vehicle({ id: 'a', displayStatus: 'ACTIVE' }),
      vehicle({ id: 'b', displayStatus: 'IDLE' }),
      vehicle({ id: 'c', displayStatus: 'ACTIVE' }),
      vehicle({ id: 'd', displayStatus: 'OFFLINE' }),
    ];
    expect(computeActiveNowCount(vehicles)).toBe(2);
  });

  it('returns zero when nothing is active', () => {
    expect(computeActiveNowCount([vehicle({ displayStatus: 'OFFLINE' })])).toBe(0);
  });
});

describe('deriveConnectionState', () => {
  const now = 1_000_000_000_000;

  it('returns live while snapshots are fresh', () => {
    expect(deriveConnectionState('live', now - 5000, now)).toBe('live');
  });

  it('reports stale once the last snapshot is older than the stale window', () => {
    expect(deriveConnectionState('live', now - SNAPSHOT_STALE_MS - 1000, now)).toBe('stale');
  });

  it('passes through non-live states unchanged', () => {
    expect(deriveConnectionState('connecting', now, now)).toBe('connecting');
    expect(deriveConnectionState('syncing', now, now)).toBe('syncing');
    expect(deriveConnectionState('offline', now, now)).toBe('offline');
  });

  it('defaults unknown states to offline', () => {
    expect(deriveConnectionState(null, now, now)).toBe('offline');
    expect(deriveConnectionState(undefined, null, now)).toBe('offline');
  });
});

describe('rankVehiclesForTriage', () => {
  it('ranks critical: live events or critical/high alerts', () => {
    const vehicles = [
      vehicle({ id: 'a' }),
      vehicle({ id: 'b' }),
    ];
    const alerts = [
      adaptedAlert({ alert_id: 'x', vehicle_id: 'b', severity: 'high' }),
    ];
    const liveEvents = [liveEvent('a', 'Speeding')];
    const rows = rankVehiclesForTriage(vehicles, { alerts, liveEvents, workItems: [] });
    const byId = Object.fromEntries(rows.map((r) => [r.id, r]));
    expect(byId.a.level).toBe('critical');
    expect(byId.a.liveEventCount).toBe(1);
    expect(byId.b.level).toBe('critical');
    expect(byId.b.criticalHighAlertCount).toBe(1);
  });

  it('ranks high for overdue maintenance or critical health', () => {
    const vehicles = [
      vehicle({ id: 'a', healthCategory: 'critical', healthStatus: 'critical', healthScore: 55 }),
      vehicle({ id: 'b' }),
    ];
    const workItems = [
      workItem({ vehicle_id: 'b', dueStatus: 'overdue', remaining_km: -200 }),
    ];
    const rows = rankVehiclesForTriage(vehicles, { alerts: [], liveEvents: [], workItems });
    const byId = Object.fromEntries(rows.map((r) => [r.id, r]));
    expect(byId.a.level).toBe('high');
    expect(byId.a.reasons).toContain('Critical health');
    expect(byId.b.level).toBe('high');
    expect(byId.b.maintenanceActionable).toBe(1);
  });

  it('ranks medium for any active alert, health warning, or scheduled maintenance', () => {
    const vehicles = [
      vehicle({ id: 'a', healthCategory: 'warning', healthStatus: 'warning', healthScore: 80 }),
      vehicle({ id: 'b' }),
      vehicle({ id: 'c' }),
    ];
    const alerts = [
      adaptedAlert({ alert_id: 'x', vehicle_id: 'b', severity: 'low' }),
    ];
    const workItems = [
      workItem({ vehicle_id: 'c', dueStatus: 'scheduled', remaining_km: 1500 }),
    ];
    const rows = rankVehiclesForTriage(vehicles, { alerts, liveEvents: [], workItems });
    const byId = Object.fromEntries(rows.map((r) => [r.id, r]));
    expect(byId.a.level).toBe('medium');
    expect(byId.b.level).toBe('medium');
    expect(byId.c.level).toBe('medium');
  });

  it('ranks stale for offline display status', () => {
    const vehicles = [vehicle({ id: 'a', displayStatus: 'OFFLINE' })];
    const rows = rankVehiclesForTriage(vehicles, { alerts: [], liveEvents: [], workItems: [] });
    expect(rows[0].level).toBe('stale');
    expect(rows[0].reasons).toContain('No live telemetry');
  });

  it('ranks normal otherwise', () => {
    const vehicles = [vehicle({ id: 'a', displayStatus: 'ACTIVE' })];
    const rows = rankVehiclesForTriage(vehicles, { alerts: [], liveEvents: [], workItems: [] });
    expect(rows[0].level).toBe('normal');
  });

  it('orders rows by level, then severity-weighted risk desc', () => {
    const vehicles = [
      vehicle({ id: 'a' }),
      vehicle({ id: 'b' }),
      vehicle({ id: 'c', displayStatus: 'OFFLINE' }),
    ];
    const alerts = [
      adaptedAlert({ alert_id: '1', vehicle_id: 'a', severity: 'critical' }),
      adaptedAlert({ alert_id: '2', vehicle_id: 'a', severity: 'medium' }),
      adaptedAlert({ alert_id: '3', vehicle_id: 'b', severity: 'high' }),
    ];
    const rows = rankVehiclesForTriage(vehicles, { alerts, liveEvents: [], workItems: [] });
    expect(rows.map((r) => r.id)).toEqual(['a', 'b', 'c']);
    expect(rows[0].riskScore).toBe(7);
    expect(rows[1].riskScore).toBe(4);
  });
});

describe('summarizeAttention', () => {
  it('counts non-normal rows by level and totals them', () => {
    const rows = [
      { level: 'critical' },
      { level: 'critical' },
      { level: 'high' },
      { level: 'medium' },
      { level: 'stale' },
      { level: 'normal' },
      { level: 'normal' },
    ];
    expect(summarizeAttention(rows)).toEqual({
      critical: 2,
      high: 1,
      medium: 1,
      stale: 1,
      total: 5,
    });
  });
});

describe('buildMaintenancePressureRows', () => {
  const fleetMeta = {
    'v-1': { vehicle_name: 'V-101', driver_name: 'Ada', odometer_km: 100000, overall_health_score: 92 },
    'v-2': { vehicle_name: 'V-102', driver_name: null, odometer_km: 95000, overall_health_score: 88 },
  };

  it('keeps only vehicles with actionable work', () => {
    const workItems = [
      workItem({ vehicle_id: 'v-1', dueStatus: 'overdue', remaining_km: -100 }),
      workItem({ vehicle_id: 'v-2', dueStatus: 'future', remaining_km: 5000 }),
    ];
    const rows = buildMaintenancePressureRows(workItems, fleetMeta);
    expect(rows).toHaveLength(1);
    expect(rows[0].vehicle_id).toBe('v-1');
    expect(rows[0].level).toBe('critical');
    expect(rows[0].actionable).toBe(1);
  });

  it('joins the nearest work item for the due label', () => {
    const workItems = [
      workItem({ vehicle_id: 'v-1', workKey: 'v-1::oil', maintenance_type: 'oil_change', maintenanceTypeLabel: 'Oil Change', dueStatus: 'scheduled', remaining_km: 1500 }),
      workItem({ vehicle_id: 'v-1', workKey: 'v-1::brakes', maintenance_type: 'brake_inspection', maintenanceTypeLabel: 'Brake Inspection', dueStatus: 'dueSoon', remaining_km: 200 }),
    ];
    const rows = buildMaintenancePressureRows(workItems, fleetMeta);
    expect(rows[0].dueLabel).toBe('200 km');
    expect(rows[0].serviceLabel).toBe('Brake Inspection');
  });
});

describe('driverRankingQuality', () => {
  function driver(score) {
    return { historical: { safetyScore: score } };
  }

  it('returns no-data when no driver is scored', () => {
    expect(driverRankingQuality([driver(null), driver(undefined)])).toBe('no-data');
    expect(driverRankingQuality([])).toBe('no-data');
  });

  it('returns degraded when the best score is implausibly low', () => {
    expect(driverRankingQuality([driver(2), driver(8)])).toBe('degraded');
  });

  it('returns ok when a meaningful score exists', () => {
    expect(driverRankingQuality([driver(0), driver(72)])).toBe('ok');
  });
});
