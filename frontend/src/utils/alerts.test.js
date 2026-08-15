import { describe, expect, it } from 'vitest';
import {
  computeAlertKpis,
  computeActiveSeverityDistribution,
  computeActiveCategoryDistribution,
  computeVehicleRisk,
  groupAlertsIntoIncidents,
  alertStaleness,
  isStaleActive,
  computeInsights,
  categoryDisplayLabel,
  formatEventCounts,
  SEVERITY_WEIGHTS,
} from './alerts';

const NOW = Date.parse('2026-08-15T12:00:00Z');

function alert(overrides = {}) {
  return {
    alert_id: 'a-1',
    vehicle_id: 'v-1',
    driver_id: null,
    trip_id: null,
    alert_type: 'health',
    severity: 'medium',
    status: 'active',
    acknowledged: false,
    acknowledged_at: null,
    created_at: '2026-08-15T08:00:00Z',
    resolved_at: null,
    condition: null,
    category: null,
    message: null,
    evidence: null,
    source: 'alert_engine',
    ...overrides,
  };
}

describe('computeAlertKpis', () => {
  it('counts critical/high/unacknowledged over ACTIVE alerts only', () => {
    const list = [
      alert({ alert_id: 'a1', severity: 'critical', status: 'active' }),
      alert({ alert_id: 'a2', severity: 'high', status: 'active', acknowledged: true }),
      alert({ alert_id: 'a3', severity: 'medium', status: 'active' }),
      alert({ alert_id: 'a4', severity: 'low', status: 'resolved' }),
      alert({ alert_id: 'a5', severity: 'critical', status: 'resolved' }),
      alert({ alert_id: 'a6', severity: 'info', status: 'active' }),
    ];
    const kpis = computeAlertKpis(list, NOW);
    expect(kpis.critical).toBe(1);
    expect(kpis.high).toBe(1);
    expect(kpis.active).toBe(4);
    expect(kpis.unacknowledged).toBe(3);
  });

  it('counts resolved24h from resolved_at within the last 24h', () => {
    const list = [
      alert({ alert_id: 'r1', status: 'resolved', resolved_at: '2026-08-15T10:00:00Z' }),
      alert({ alert_id: 'r2', status: 'resolved', resolved_at: '2026-08-14T09:00:00Z' }),
      alert({ alert_id: 'r3', status: 'resolved', resolved_at: null }),
      alert({ alert_id: 'a1', status: 'active' }),
    ];
    expect(computeAlertKpis(list, NOW).resolved24h).toBe(1);
  });
});

describe('computeActiveSeverityDistribution', () => {
  it('covers only active alerts and drops zero slices', () => {
    const list = [
      alert({ alert_id: 'a1', severity: 'critical' }),
      alert({ alert_id: 'a2', severity: 'high', acknowledged: true }),
      alert({ alert_id: 'a3', severity: 'low', status: 'resolved' }),
    ];
    const dist = computeActiveSeverityDistribution(list);
    expect(dist).toHaveLength(2);
    expect(dist[0].key).toBe('critical');
    expect(dist.reduce((s, d) => s + d.count, 0)).toBe(2);
  });
});

describe('categoryDisplayLabel and distribution', () => {
  it('renders null category as Unclassified, never Other', () => {
    expect(categoryDisplayLabel(null)).toBe('Unclassified');
    expect(categoryDisplayLabel(undefined)).toBe('Unclassified');
    expect(categoryDisplayLabel('safety_driving')).toBe('Safety & Driving');
  });

  it('counts active alerts by category and surfaces Unclassified keyed as null', () => {
    const list = [
      alert({ alert_id: 'a1', category: null }),
      alert({ alert_id: 'a2', category: null }),
      alert({ alert_id: 'a3', category: 'safety_driving' }),
      alert({ alert_id: 'a4', category: 'safety_driving', status: 'resolved' }),
    ];
    const dist = computeActiveCategoryDistribution(list);
    const unclassified = dist.find((d) => d.key === null);
    const safety = dist.find((d) => d.key === 'safety_driving');
    expect(dist.reduce((s, d) => s + d.count, 0)).toBe(3);
    expect(unclassified.count).toBe(2);
    expect(unclassified.label).toBe('Unclassified');
    expect(safety.count).toBe(1);
    expect(dist[0].count).toBeGreaterThanOrEqual(dist[1].count);
  });
});

describe('computeVehicleRisk', () => {
  it('weights active alerts by severity and sorts descending', () => {
    const list = [
      alert({ alert_id: 'a1', vehicle_id: 'v-1', severity: 'critical', category: 'safety_driving' }),
      alert({ alert_id: 'a2', vehicle_id: 'v-1', severity: 'high', acknowledged: true }),
      alert({ alert_id: 'a3', vehicle_id: 'v-1', severity: 'medium', category: 'safety_driving' }),
      alert({ alert_id: 'a4', vehicle_id: 'v-2', severity: 'info' }),
      alert({ alert_id: 'a5', vehicle_id: 'v-2', severity: 'low', status: 'resolved' }),
    ];
    const risk = computeVehicleRisk(list);
    expect(risk[0].vehicle_id).toBe('v-1');
    expect(risk[0].riskScore).toBe(
      SEVERITY_WEIGHTS.critical + SEVERITY_WEIGHTS.high + SEVERITY_WEIGHTS.medium
    );
    expect(risk[0].activeCount).toBe(3);
    expect(risk[0].criticalHighCount).toBe(2);
    expect(risk[0].dominantCategory).toBe('Safety & Driving');
    expect(risk[1].vehicle_id).toBe('v-2');
    expect(risk[1].riskScore).toBe(0);
  });
});

describe('groupAlertsIntoIncidents', () => {
  it('groups alerts sharing a trip_id into one incident', () => {
    const list = [
      alert({ alert_id: 'g1', trip_id: 't-1', severity: 'high', evidence: { event_counts: { total: 10, harsh_braking: 3 } } }),
      alert({ alert_id: 'g2', trip_id: 't-1', severity: 'critical', acknowledged: true, evidence: { event_counts: { total: 20, severe: 2 } }, created_at: '2026-08-15T07:00:00Z' }),
    ];
    const incidents = groupAlertsIntoIncidents(list);
    expect(incidents).toHaveLength(1);
    const inc = incidents[0];
    expect(inc.groupCount).toBe(2);
    expect(inc.alert_ids).toEqual(['g1', 'g2']);
    expect(inc.severity).toBe('critical');
    expect(inc.status).toBe('active');
    expect(inc.acknowledged).toBe(false);
    expect(inc.created_at).toBe('2026-08-15T07:00:00.000Z');
    expect(inc.eventCounts).toEqual({ total: 30, harsh_braking: 3, severe: 2 });
  });

  it('keeps alerts without a trip_id independent', () => {
    const list = [
      alert({ alert_id: 's1' }),
      alert({ alert_id: 's2', trip_id: 't-9' }),
      alert({ alert_id: 's3', trip_id: 't-9', status: 'resolved', acknowledged: true, resolved_at: '2026-08-15T09:00:00Z' }),
    ];
    const incidents = groupAlertsIntoIncidents(list);
    expect(incidents).toHaveLength(2);
    expect(incidents.find((i) => i.key === 'alert:s1').groupCount).toBe(1);
    const tripInc = incidents.find((i) => i.key === 'trip:t-9');
    expect(tripInc.groupCount).toBe(2);
    expect(tripInc.status).toBe('active');
  });

  it('sorts incidents severity desc then newest first', () => {
    const list = [
      alert({ alert_id: 'm1', severity: 'medium' }),
      alert({ alert_id: 'c1', severity: 'critical', created_at: '2026-08-15T06:00:00Z' }),
      alert({ alert_id: 'c2', severity: 'critical', created_at: '2026-08-15T10:00:00Z' }),
    ];
    const incidents = groupAlertsIntoIncidents(list);
    expect(incidents.map((i) => i.alert_ids[0])).toEqual(['c2', 'c1', 'm1']);
  });
});

describe('staleness', () => {
  it('classifies fresh/stale/hard-stale from created_at age', () => {
    expect(alertStaleness(alert({ created_at: '2026-08-15T11:00:00Z' }), NOW).level).toBe('fresh');
    expect(alertStaleness(alert({ created_at: '2026-08-14T10:00:00Z' }), NOW).level).toBe('stale');
    expect(alertStaleness(alert({ created_at: '2026-08-10T00:00:00Z' }), NOW).level).toBe('hard-stale');
    expect(alertStaleness(alert({ created_at: null }), NOW).level).toBe('unknown');
  });

  it('never flags resolved alerts as stale', () => {
    expect(isStaleActive(alert({ status: 'resolved', created_at: '2026-08-10T00:00:00Z' }), NOW)).toBe(false);
    expect(isStaleActive(alert({ created_at: '2026-08-14T10:00:00Z' }), NOW)).toBe(true);
  });
});

describe('computeInsights', () => {
  it('emits attention/data-quality/stale callouts only when backed by data', () => {
    const list = [
      alert({ alert_id: 'a1', severity: 'critical' }),
      alert({ alert_id: 'a2', severity: 'medium', category: null }),
      alert({ alert_id: 'a3', severity: 'medium', category: null, created_at: '2026-08-10T00:00:00Z' }),
    ];
    const insights = computeInsights(list, NOW);
    expect(insights.some((i) => i.kind === 'ATTENTION' && i.text.includes('1 critical alert'))).toBe(true);
    expect(insights.some((i) => i.kind === 'DATA QUALITY')).toBe(true);
    expect(insights.some((i) => i.kind === 'STALE')).toBe(true);
  });

  it('emits nothing when the dataset is empty', () => {
    expect(computeInsights([], NOW)).toEqual([]);
  });
});

describe('reconciliation', () => {
  it('all active surfaces agree on the active population', () => {
    const list = [
      alert({ alert_id: 'a1', severity: 'critical', category: 'safety_driving', vehicle_id: 'v-1' }),
      alert({ alert_id: 'a2', severity: 'high', category: 'safety_driving', vehicle_id: 'v-1', acknowledged: true }),
      alert({ alert_id: 'a3', severity: 'medium', category: null, vehicle_id: 'v-2' }),
      alert({ alert_id: 'a4', severity: 'low', status: 'resolved', vehicle_id: 'v-2' }),
    ];
    const kpis = computeAlertKpis(list, NOW);
    const sev = computeActiveSeverityDistribution(list);
    const cat = computeActiveCategoryDistribution(list);
    const risk = computeVehicleRisk(list);

    expect(sev.reduce((s, d) => s + d.count, 0)).toBe(kpis.active);
    expect(cat.reduce((s, d) => s + d.count, 0)).toBe(kpis.active);
    expect(risk.reduce((s, v) => s + v.activeCount, 0)).toBe(kpis.active);
  });
});

describe('formatEventCounts', () => {
  it('builds a compact ordered summary and returns null when empty', () => {
    expect(formatEventCounts({ total: 134, severe: 54, harsh_braking: 3 })).toBe('134 events · 3 braking · 54 severe');
    expect(formatEventCounts(null)).toBeNull();
    expect(formatEventCounts({})).toBeNull();
  });
});
