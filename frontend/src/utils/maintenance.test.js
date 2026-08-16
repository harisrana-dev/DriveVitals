import { describe, expect, it } from 'vitest';
import {
  computeMaintenanceStatus,
  computeMaintenanceKpis,
  computeVehicleMaintenanceRisk,
  computeServiceWorkload,
  computeMaintenanceHorizon,
  computeMaintenanceInsights,
  normalizeMaintenanceRecords,
  groupMaintenanceWorkItems,
  filterMaintenanceWorkItems,
  sortMaintenanceWorkItems,
  sortMaintenanceHistory,
  dueStatus,
  maintenanceTypeLabel,
  formatMaintenanceDue,
  MAINTENANCE_TYPE_LABELS,
} from './maintenance';

const FLEET_META = {
  'v-1': { vehicle_name: 'Volvo VNR-260', driver_name: 'Alice Smith', odometer_km: 120000, overall_health_score: 84, overall_health_status: 'healthy' },
  'v-2': { vehicle_name: 'Volvo VNL-300', driver_name: null, odometer_km: 95000, overall_health_score: 61, overall_health_status: 'warning' },
};

function record(overrides = {}) {
  return {
    id: 'v-1:oil_change',
    vehicle_id: 'v-1',
    maintenance_type: 'oil_change',
    priority: 'high',
    status: 'pending',
    due_odometer_km: 120500,
    created_at: '2026-08-01T08:00:00Z',
    component: 'Engine',
    reason: 'Scheduled interval reached',
    recommended_action: 'Replace oil and filter',
    estimated_cost: null,
    ...overrides,
  };
}

describe('computeMaintenanceStatus', () => {
  it('marks 0 or negative remaining as overdue', () => {
    expect(computeMaintenanceStatus(0).key).toBe('overdue');
    expect(computeMaintenanceStatus(-500).key).toBe('overdue');
  });

  it('marks 1..500 remaining as dueSoon and 501..2000 as scheduled', () => {
    expect(computeMaintenanceStatus(1).key).toBe('dueSoon');
    expect(computeMaintenanceStatus(500).key).toBe('dueSoon');
    expect(computeMaintenanceStatus(501).key).toBe('scheduled');
    expect(computeMaintenanceStatus(2000).key).toBe('scheduled');
  });

  it('marks beyond 2000 as future', () => {
    expect(computeMaintenanceStatus(2001).key).toBe('future');
  });

  it('falls back to due_date when remaining km is unknown', () => {
    const past = { due_date: new Date(Date.now() - 86400000).toISOString() };
    const soon = { due_date: new Date(Date.now() + 3 * 86400000).toISOString() };
    const later = { due_date: new Date(Date.now() + 21 * 86400000).toISOString() };
    expect(computeMaintenanceStatus(null, past).key).toBe('overdue');
    expect(computeMaintenanceStatus(null, soon).key).toBe('dueSoon');
    expect(computeMaintenanceStatus(null, later).key).toBe('scheduled');
  });

  it('returns future when neither km nor a valid date is available', () => {
    expect(computeMaintenanceStatus(null, {}).key).toBe('future');
  });
});

describe('dueStatus (legacy)', () => {
  it('keeps the legacy thresholds for drawer consumers', () => {
    expect(dueStatus(-5)).toBe('OVERDUE');
    expect(dueStatus(0)).toBe('OVERDUE');
    expect(dueStatus(300)).toBe('DUE SOON');
    expect(dueStatus(1500)).toBe('SCHEDULED');
    expect(dueStatus(5000)).toBe('GOOD');
  });
});

describe('normalizeMaintenanceRecords', () => {
  it('joins fleet meta and computes remaining_km', () => {
    const rows = normalizeMaintenanceRecords([record()], FLEET_META);
    expect(rows[0].vehicle_name).toBe('Volvo VNR-260');
    expect(rows[0].driver_name).toBe('Alice Smith');
    expect(rows[0].odometer_km).toBe(120000);
    expect(rows[0].remaining_km).toBe(500);
    expect(rows[0].dueStatus).toBe('dueSoon');
    expect(rows[0].maintenanceTypeLabel).toBe('Oil Change');
  });

  it('leaves remaining_km null when odometer is unknown', () => {
    const rows = normalizeMaintenanceRecords([record()], { 'v-1': {} });
    expect(rows[0].remaining_km).toBe(null);
  });

  it('survives non-array input', () => {
    expect(normalizeMaintenanceRecords(null, FLEET_META)).toEqual([]);
  });
});

describe('groupMaintenanceWorkItems', () => {
  it('groups by (vehicle_id, maintenance_type) and discloses projections', () => {
    const items = groupMaintenanceWorkItems([
      record({ id: 'v-1:oil_change' }),
      record({ id: 'v-1:oil_change:legacy' }),
      record({ id: 'v-1:brake_inspection', maintenance_type: 'brake_inspection' }),
    ]);
    expect(items).toHaveLength(2);
    const oil = items.find((i) => i.maintenance_type === 'oil_change');
    expect(oil.projectionCount).toBe(2);
    expect(oil.projections).toHaveLength(2);
    const brakes = items.find((i) => i.maintenance_type === 'brake_inspection');
    expect(brakes.projectionCount).toBe(1);
  });
});

describe('computeMaintenanceKpis', () => {
  function row(remaining, dueStatusKey) {
    return { ...record(), remaining_km: remaining, dueStatus: dueStatusKey };
  }

  it('counts overdue, dueSoon and the 2,000 km window', () => {
    const items = [
      row(-100, 'overdue'),
      row(400, 'dueSoon'),
      row(1900, 'scheduled'),
      row(5000, 'future'),
    ];
    const kpis = computeMaintenanceKpis(items);
    expect(kpis.overdue).toBe(1);
    expect(kpis.dueSoon).toBe(1);
    expect(kpis.dueWithin2000).toBe(3);
    expect(kpis.total).toBe(4);
  });

  it('counts distinct vehicles requiring service', () => {
    const items = [
      row(-100, 'overdue'),
      { ...row(300, 'dueSoon'), vehicle_id: 'v-1' },
      { ...row(1900, 'scheduled'), vehicle_id: 'v-2' },
      { ...row(5000, 'future'), vehicle_id: 'v-3' },
    ];
    expect(computeMaintenanceKpis(items).vehiclesRequiringService).toBe(2);
  });
});

describe('computeVehicleMaintenanceRisk', () => {
  const base = {
    ...record(),
    maintenance_type: 'brake_inspection',
    dueStatus: 'scheduled',
    priority: 'medium',
    vehicle_id: 'v-1',
    vehicle_name: 'Volvo VNR-260',
  };

  it('escalates level by worst status and ranks critical first', () => {
    const items = [
      { ...base, vehicle_id: 'v-1', vehicle_name: 'Volvo VNR-260', dueStatus: 'dueSoon' },
      { ...base, vehicle_id: 'v-2', vehicle_name: 'Volvo VNL-300', dueStatus: 'overdue' },
      { ...base, vehicle_id: 'v-3', vehicle_name: 'Volvo VNM-200', dueStatus: 'future' },
    ];
    const risk = computeVehicleMaintenanceRisk(items, FLEET_META);
    expect(risk[0].vehicle_id).toBe('v-2');
    expect(risk[0].level).toBe('critical');
    expect(risk[1].vehicle_id).toBe('v-1');
    expect(risk[1].level).toBe('high');
    expect(risk[2].vehicle_id).toBe('v-3');
    expect(risk[2].level).toBe('good');
  });

  it('counts actionable items per vehicle', () => {
    const items = [
      { ...base, dueStatus: 'overdue' },
      { ...base, dueStatus: 'scheduled' },
      { ...base, dueStatus: 'future' },
    ];
    const risk = computeVehicleMaintenanceRisk(items, FLEET_META);
    expect(risk[0].actionable).toBe(2);
    expect(risk[0].overdue).toBe(1);
    expect(risk[0].future).toBe(1);
  });
});

describe('computeServiceWorkload', () => {
  it('aggregates totals and urgency per service type', () => {
    const items = [
      { ...record(), maintenance_type: 'oil_change', maintenanceTypeLabel: 'Oil Change', dueStatus: 'overdue' },
      { ...record(), id: 'v-1:oil_change:2', maintenance_type: 'oil_change', maintenanceTypeLabel: 'Oil Change', dueStatus: 'dueSoon' },
      { ...record(), id: 'v-1:brake_inspection', maintenance_type: 'brake_inspection', maintenanceTypeLabel: 'Brake Inspection', dueStatus: 'future' },
    ];
    const workload = computeServiceWorkload(items);
    const oil = workload.find((w) => w.maintenance_type === 'oil_change');
    expect(oil.total).toBe(2);
    expect(oil.overdue).toBe(1);
    expect(oil.dueSoon).toBe(1);
    expect(workload[0].maintenance_type).toBe('oil_change');
  });
});

describe('computeMaintenanceHorizon', () => {
  const now = Date.parse('2026-08-16T12:00:00Z');

  it('returns null when no record carries a due_date', () => {
    const items = [record({ due_date: null })];
    expect(computeMaintenanceHorizon(items, now)).toBe(null);
  });

  it('buckets dated items and reports coverage', () => {
    const items = [
      record({ id: 'v-1:a', due_date: '2026-08-15T00:00:00Z' }),
      record({ id: 'v-1:b', due_date: '2026-08-18T00:00:00Z' }),
      record({ id: 'v-1:c', due_date: '2026-08-25T00:00:00Z' }),
      record({ id: 'v-1:d', due_date: null }),
    ];
    const horizon = computeMaintenanceHorizon(items, now);
    expect(horizon.coverage).toBeCloseTo(0.75);
    expect(horizon.buckets.find((b) => b.key === 'overdue').count).toBe(1);
    expect(horizon.buckets.find((b) => b.key === 'week').count).toBe(1);
    expect(horizon.buckets.find((b) => b.key === 'twoWeeks').count).toBe(1);
  });
});

describe('computeMaintenanceInsights', () => {
  it('flags overdue work items', () => {
    const insights = computeMaintenanceInsights(
      [{ ...record(), dueStatus: 'overdue' }],
      []
    );
    expect(insights.some((i) => i.key === 'overdue-work')).toBe(true);
  });

  it('flags converging service windows for vehicles with multiple actionable items', () => {
    const vehicleRisk = [
      { vehicle_id: 'v-1', vehicle_name: 'Volvo VNR-260', actionable: 3, overdue: 1, dueSoon: 1 },
      { vehicle_id: 'v-2', vehicle_name: 'Volvo VNL-300', actionable: 1, overdue: 0, dueSoon: 1 },
    ];
    const insights = computeMaintenanceInsights(
      [{ ...record(), dueStatus: 'dueSoon' }],
      vehicleRisk
    );
    const convergence = insights.find((i) => i.key === 'convergence');
    expect(convergence).toBeDefined();
    expect(convergence.body).toContain('Volvo VNR-260');
  });

  it('flags low-health vehicles with service due', () => {
    const vehicleRisk = [
      { vehicle_id: 'v-2', vehicle_name: 'Volvo VNL-300', overall_health_score: 61, actionable: 2 },
    ];
    const insights = computeMaintenanceInsights(
      [{ ...record(), dueStatus: 'scheduled' }],
      vehicleRisk
    );
    expect(insights.some((i) => i.key === 'low-health')).toBe(true);
  });

  it('reports the most common service type', () => {
    const insights = computeMaintenanceInsights(
      [{ ...record(), dueStatus: 'future' }],
      []
    );
    expect(insights.some((i) => i.key === 'workload')).toBe(true);
  });

  it('returns no insights for an empty fleet', () => {
    expect(computeMaintenanceInsights([], [])).toEqual([]);
  });
});

describe('filterMaintenanceWorkItems', () => {
  const items = [
    { ...record(), dueStatus: 'overdue', priority: 'critical', maintenance_type: 'oil_change', vehicle_name: 'Volvo VNR-260', driver_name: 'Alice Smith' },
    { ...record(), id: 'v-1:brakes', dueStatus: 'dueSoon', priority: 'high', maintenance_type: 'brake_inspection', vehicle_name: 'Volvo VNR-260', driver_name: 'Alice Smith' },
    { ...record(), id: 'v-2:coolant', vehicle_id: 'v-2', dueStatus: 'scheduled', priority: 'medium', maintenance_type: 'coolant_flush', vehicle_name: 'Volvo VNL-300', driver_name: null },
  ];

  it('filters by status tab', () => {
    expect(filterMaintenanceWorkItems(items, { statusTab: 'overdue' })).toHaveLength(1);
  });

  it('filters to the due-within-2,000km population', () => {
    const out = filterMaintenanceWorkItems(items, { dueWithin2000: true });
    expect(out).toHaveLength(3);
  });

  it('filters by priority and service type', () => {
    expect(filterMaintenanceWorkItems(items, { priority: 'high' })).toHaveLength(1);
    expect(filterMaintenanceWorkItems(items, { type: 'coolant_flush' })).toHaveLength(1);
  });

  it('filters by vehicle and driver search', () => {
    expect(filterMaintenanceWorkItems(items, { vehicleSearch: 'VNL' })).toHaveLength(1);
    expect(filterMaintenanceWorkItems(items, { driverSearch: 'alice' })).toHaveLength(2);
  });

  it('survives non-array input', () => {
    expect(filterMaintenanceWorkItems(null, {})).toEqual([]);
  });
});

describe('sortMaintenanceWorkItems', () => {
  const items = [
    { ...record(), id: 'a', dueStatus: 'future', priority: 'medium', remaining_km: 5000, vehicle_name: 'B' },
    { ...record(), id: 'b', dueStatus: 'overdue', priority: 'low', remaining_km: -100, vehicle_name: 'A' },
    { ...record(), id: 'c', dueStatus: 'dueSoon', priority: 'critical', remaining_km: 300, vehicle_name: 'C' },
  ];

  it('sorts by status then priority by default', () => {
    const out = sortMaintenanceWorkItems(items);
    expect(out.map((i) => i.id)).toEqual(['b', 'c', 'a']);
  });

  it('sorts by priority first', () => {
    const out = sortMaintenanceWorkItems(items, 'priority');
    expect(out[0].id).toBe('c');
  });

  it('sorts by remaining km', () => {
    const out = sortMaintenanceWorkItems(items, 'remaining');
    expect(out.map((i) => i.id)).toEqual(['b', 'c', 'a']);
  });

  it('sorts by vehicle name', () => {
    const out = sortMaintenanceWorkItems(items, 'vehicle');
    expect(out.map((i) => i.id)).toEqual(['b', 'a', 'c']);
  });
});

describe('sortMaintenanceHistory', () => {
  it('returns completed records only, newest first', () => {
    const rows = sortMaintenanceHistory(
      [
        record({ id: 'c1', status: 'completed', completed_at: '2026-08-10T08:00:00Z', maintenance_type: 'oil_change' }),
        record({ id: 'p1', status: 'pending' }),
        record({ id: 'c2', status: 'completed', completed_at: '2026-08-14T08:00:00Z', maintenance_type: 'brake_inspection' }),
      ],
      FLEET_META
    );
    expect(rows).toHaveLength(2);
    expect(rows[0].id).toBe('c2');
    expect(rows[1].id).toBe('c1');
    expect(rows[0].vehicle_name).toBe('Volvo VNR-260');
  });
});

describe('formatMaintenanceDue', () => {
  it('formats remaining km and overdue distance', () => {
    expect(formatMaintenanceDue({ remaining_km: 1500 })).toBe('1,500 km');
    expect(formatMaintenanceDue({ remaining_km: 0 })).toBe('Due now');
    expect(formatMaintenanceDue({ remaining_km: -250 })).toBe('Overdue by 250 km');
  });

  it('falls back to the due date when km is unknown', () => {
    const d = formatMaintenanceDue({ remaining_km: null, due_date: '2026-08-30T00:00:00Z' });
    expect(d).toMatch(/Aug 30/);
    expect(formatMaintenanceDue({ remaining_km: null, due_date: null })).toBe('\u2014');
  });
});

describe('maintenanceTypeLabel', () => {
  it('maps known types and title-cases unknowns', () => {
    expect(MAINTENANCE_TYPE_LABELS.oil_change).toBe('Oil Change');
    expect(maintenanceTypeLabel('oil_change')).toBe('Oil Change');
    expect(maintenanceTypeLabel('custom_service')).toBe('Custom Service');
    expect(maintenanceTypeLabel()).toBe('Service');
  });
});
