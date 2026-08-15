import { describe, expect, it } from 'vitest';
import {
  adaptAlert,
  adaptAlerts,
  applyAlertEvent,
  severityLabel,
  severityRank,
  categoryLabel,
} from './alertAdapter';

const restAlert = {
  alert_id: 'trip_unsafe:v-101',
  vehicle_id: 'v-101',
  driver_id: 'd-7',
  trip_id: 't-9',
  alert_type: 'trip',
  severity: 'critical',
  status: 'active',
  acknowledged: false,
  acknowledged_at: null,
  created_at: '2026-08-15T08:00:00Z',
  resolved_at: null,
  condition: 'trip_unsafe',
  category: 'safety_driving',
  message: 'Harsh braking detected on route',
  evidence: { event_counts: { harsh_braking: 3 } },
  source: 'alert_engine',
};

const meta = {
  'v-101': {
    vehicle_name: 'Truck 101',
    driver_name: 'Alice Smith',
  },
};

describe('adaptAlert', () => {
  it('maps canonical fields verbatim without fabrication', () => {
    const view = adaptAlert(restAlert, meta['v-101']);
    expect(view.id).toBe('trip_unsafe:v-101');
    expect(view.alert_id).toBe('trip_unsafe:v-101');
    expect(view.vehicle_id).toBe('v-101');
    expect(view.vehicle_name).toBe('Truck 101');
    expect(view.driver_name).toBe('Alice Smith');
    expect(view.trip_id).toBe('t-9');
    expect(view.condition).toBe('trip_unsafe');
    expect(view.category).toBe('safety_driving');
    expect(view.message).toBe('Harsh braking detected on route');
    expect(view.evidence).toEqual({ event_counts: { harsh_braking: 3 } });
    expect(view.source).toBe('alert_engine');
    expect(view.severity).toBe('critical');
    expect(view.status).toBe('active');
    expect(view.acknowledged).toBe(false);
    expect(view.acknowledged_at).toBeNull();
    expect(view.created_at).toBe('2026-08-15T08:00:00Z');
    expect(view.resolved_at).toBeNull();
  });

  it('never defaults category or invents telemetry/health', () => {
    const view = adaptAlert(restAlert, null);
    expect(view.category).toBe('safety_driving');
    expect(view.category).not.toBe('Engine');
    expect(view.vehicle_name).toBeNull();
    expect(view.driver_name).toBeNull();
    expect(view.message).toBeTruthy();
    expect('speed' in view).toBe(false);
    expect('rpm' in view).toBe(false);
    expect('overall_health_score' in view).toBe(false);
  });

  it('keeps null unknowns as null', () => {
    const minimal = {
      alert_id: 'a-1',
      vehicle_id: 'v-1',
      alert_type: 'health',
      severity: 'medium',
      status: 'resolved',
      acknowledged: true,
      acknowledged_at: '2026-08-15T09:00:00Z',
      created_at: '2026-08-15T08:00:00Z',
      resolved_at: '2026-08-15T09:30:00Z',
    };
    const view = adaptAlert(minimal, null);
    expect(view.condition).toBeNull();
    expect(view.category).toBeNull();
    expect(view.message).toBeNull();
    expect(view.evidence).toBeNull();
    expect(view.driver_id).toBeNull();
    expect(view.trip_id).toBeNull();
    expect(view.vehicle_name).toBeNull();
  });

  it('maps resolved status to resolved', () => {
    const view = adaptAlert({ ...restAlert, status: 'resolved', acknowledged: true }, null);
    expect(view.status).toBe('resolved');
    expect(view.acknowledged).toBe(true);
  });
});

describe('adaptAlerts', () => {
  it('resolves names through fleet meta by vehicle id', () => {
    const views = adaptAlerts([restAlert], meta);
    expect(views[0].vehicle_name).toBe('Truck 101');
    expect(views[0].driver_name).toBe('Alice Smith');
  });

  it('returns [] for non-array input', () => {
    expect(adaptAlerts(null, meta)).toEqual([]);
    expect(adaptAlerts(undefined, meta)).toEqual([]);
  });
});

describe('applyAlertEvent', () => {
  it('appends a created event when the id is unknown', () => {
    const event = {
      type: 'alert_created',
      alert_id: 'trip_unsafe:v-101',
      vehicle_id: 'v-101',
      driver_id: 'd-7',
      trip_id: 't-9',
      alert_type: 'trip',
      severity: 'critical',
      category: 'safety_driving',
      condition: 'trip_unsafe',
      message: 'Harsh braking detected on route',
      evidence: { event_counts: { harsh_braking: 3 } },
      source: 'alert_engine',
      created_at: '2026-08-15T08:00:00Z',
    };
    const next = applyAlertEvent([], event);
    expect(next).toHaveLength(1);
    expect(next[0].alert_id).toBe('trip_unsafe:v-101');
    expect(next[0].status).toBe('active');
    expect(next[0].acknowledged).toBe(false);
  });

  it('does not duplicate an existing created event', () => {
    const event = {
      type: 'alert_created',
      alert_id: 'trip_unsafe:v-101',
      vehicle_id: 'v-101',
      alert_type: 'trip',
      severity: 'critical',
      category: 'safety_driving',
    };
    const next = applyAlertEvent([restAlert], event);
    expect(next).toHaveLength(1);
  });

  it('patches an acknowledged event in place', () => {
    const event = {
      type: 'alert_acknowledged',
      alert_id: 'trip_unsafe:v-101',
      vehicle_id: 'v-101',
      acknowledged: true,
      acknowledged_at: '2026-08-15T08:05:00Z',
      status: 'active',
    };
    const next = applyAlertEvent([restAlert], event);
    expect(next).toHaveLength(1);
    expect(next[0].acknowledged).toBe(true);
    expect(next[0].acknowledged_at).toBe('2026-08-15T08:05:00Z');
    expect(next[0].status).toBe('active');
  });

  it('patches a resolved event in place', () => {
    const event = {
      type: 'alert_resolved',
      alert_id: 'trip_unsafe:v-101',
      vehicle_id: 'v-101',
      acknowledged: true,
      acknowledged_at: '2026-08-15T08:05:00Z',
      status: 'resolved',
      resolved_at: '2026-08-15T08:10:00Z',
    };
    const next = applyAlertEvent([restAlert], event);
    expect(next[0].status).toBe('resolved');
    expect(next[0].resolved_at).toBe('2026-08-15T08:10:00Z');
    expect(next[0].acknowledged).toBe(true);
  });

  it('ignores events without an id or type', () => {
    expect(applyAlertEvent([restAlert], null)).toHaveLength(1);
    expect(applyAlertEvent([restAlert], {})).toHaveLength(1);
  });
});

describe('labels', () => {
  it('maps canonical severities and ranks', () => {
    expect(severityLabel('critical')).toBe('Critical');
    expect(severityLabel('high')).toBe('High');
    expect(severityLabel('medium')).toBe('Medium');
    expect(severityLabel('low')).toBe('Low');
    expect(severityLabel('info')).toBe('Information');
    expect(severityLabel('bogus')).toBe('bogus');
    expect(severityRank('critical')).toBe(0);
    expect(severityRank('high')).toBe(1);
    expect(severityRank('medium')).toBe(2);
    expect(severityRank('low')).toBe(3);
    expect(severityRank('info')).toBe(4);
    expect(severityRank('bogus')).toBe(5);
  });

  it('maps canonical categories', () => {
    expect(categoryLabel('safety_driving')).toBe('Safety & Driving');
    expect(categoryLabel('vehicle_health')).toBe('Vehicle Health');
    expect(categoryLabel('engine')).toBe('Engine');
    expect(categoryLabel('bogus')).toBe('bogus');
    expect(categoryLabel(null)).toBeNull();
  });
});
