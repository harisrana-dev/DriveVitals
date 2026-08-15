/**
 * Alert adapter — maps backend AlertRead rows (REST) and WebSocket alert
 * events into the Alerts page view model WITHOUT fabricating data.
 *
 * Every field traces to a real backend source:
 *  - severity / status / acknowledged / timestamps come verbatim from the
 *    backend canonical contract.
 *  - category is the backend-assigned canonical category; it is NEVER
 *    inferred from the alert type and never defaulted to "Engine".
 *  - `message` and `evidence` are rendered verbatim from the backend when
 *    present and are `null` when absent (rendered as "—").
 *  - vehicle/driver names come from fleet metadata when known, else null.
 *
 * Unknown values are represented explicitly as `null` and are never
 * replaced with defaults, fabricated timestamps, telemetry or health
 * scores.
 */

const SEVERITY_LABELS = {
  critical: 'Critical',
  high: 'High',
  medium: 'Medium',
  low: 'Low',
  info: 'Information',
};

const SEVERITY_RANKS = {
  critical: 0,
  high: 1,
  medium: 2,
  low: 3,
  info: 4,
};

const CATEGORY_LABELS = {
  safety_driving: 'Safety & Driving',
  vehicle_health: 'Vehicle Health',
  cooling: 'Cooling',
  fuel: 'Fuel',
  engine: 'Engine',
  electrical: 'Electrical',
  transmission: 'Transmission',
  brakes: 'Brakes',
  maintenance: 'Maintenance',
  trip: 'Trip',
  other: 'Other',
};

export function severityLabel(severity) {
  return SEVERITY_LABELS[severity] || severity || null;
}

export function severityRank(severity) {
  return SEVERITY_RANKS[severity] ?? 5;
}

export function categoryLabel(category) {
  return CATEGORY_LABELS[category] || category || null;
}

function titleCase(value) {
  if (!value) return 'Alert';
  return String(value).replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

export function alertTitle(alert) {
  if (!alert) return 'Alert';
  return titleCase(alert.alert_type);
}

export function adaptAlert(alert, meta) {
  if (!alert) return null;
  return {
    id: alert.alert_id,
    alert_id: alert.alert_id,
    vehicle_id: alert.vehicle_id,
    vehicle_name: meta?.vehicle_name || null,
    driver_id: alert.driver_id ?? null,
    driver_name: meta?.driver_name || null,
    trip_id: alert.trip_id ?? null,
    alert_type: alert.alert_type,
    condition: alert.condition ?? null,
    category: alert.category ?? null,
    category_label: categoryLabel(alert.category),
    severity: alert.severity,
    severity_label: severityLabel(alert.severity),
    status: alert.status === 'resolved' ? 'resolved' : 'active',
    acknowledged: !!alert.acknowledged,
    acknowledged_at: alert.acknowledged_at ?? null,
    created_at: alert.created_at ?? null,
    resolved_at: alert.resolved_at ?? null,
    message: alert.message ?? null,
    evidence: alert.evidence ?? null,
    source: alert.source ?? null,
    title: alertTitle(alert),
  };
}

export function adaptAlerts(alerts, fleetMeta) {
  if (!Array.isArray(alerts)) return [];
  const meta = fleetMeta || {};
  return alerts.map((a) => adaptAlert(a, meta[a.vehicle_id]));
}

function viewFromEvent(event) {
  return {
    id: event.alert_id,
    alert_id: event.alert_id,
    vehicle_id: event.vehicle_id,
    vehicle_name: null,
    driver_id: event.driver_id ?? null,
    driver_name: null,
    trip_id: event.trip_id ?? null,
    alert_type: event.alert_type,
    condition: event.condition ?? null,
    category: event.category ?? null,
    category_label: categoryLabel(event.category),
    severity: event.severity,
    severity_label: severityLabel(event.severity),
    status: event.status || 'active',
    acknowledged: !!event.acknowledged,
    acknowledged_at: event.acknowledged_at ?? null,
    created_at: event.created_at ?? null,
    resolved_at: event.resolved_at ?? null,
    message: event.message ?? null,
    evidence: event.evidence ?? null,
    source: event.source ?? null,
    title: titleCase(event.alert_type),
  };
}

/**
 * Reconcile one WebSocket alert event into an existing alerts array.
 *
 * Events are keyed by the stored, vehicle-scoped ``alert_id`` (the same id
 * REST rows expose), so reconciliation never duplicates and never invents
 * ids. A ``alert_created`` event is only appended when the id is not already
 * present; acknowledge/resolve events patch the matching row in place.
 */
export function applyAlertEvent(alerts, event) {
  const list = Array.isArray(alerts) ? alerts : [];
  if (!event || !event.type || !event.alert_id) return list;

  const type = event.type;

  if (type === 'alert_created') {
    if (list.some((a) => a.alert_id === event.alert_id)) return list;
    return [viewFromEvent(event), ...list];
  }

  if (type === 'alert_acknowledged' || type === 'alert_resolved') {
    let changed = false;
    const next = list.map((a) => {
      if (a.alert_id !== event.alert_id) return a;
      changed = true;
      return {
        ...a,
        acknowledged: event.acknowledged ?? a.acknowledged,
        acknowledged_at: event.acknowledged_at ?? a.acknowledged_at,
        status: event.status ?? a.status,
        resolved_at: event.resolved_at ?? a.resolved_at,
      };
    });
    if (!changed) return list;
    return next;
  }

  return list;
}
