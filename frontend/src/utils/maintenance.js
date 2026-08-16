/**
 * Canonical maintenance selectors.
 *
 * Every number rendered on the Maintenance page derives from backend
 * maintenance records joined to fleet meta. Nothing here fabricates
 * service history, costs, dates or "days until due" — the previous
 * estimator-based builders (SERVICE_INTERVALS, computeNextService,
 * buildServiceHistory, buildDrawerData, ...) have been removed.
 *
 * The two legacy exports (``dueStatus`` / ``dueStatusStyle``) are kept
 * because VehicleDrawer and VehicleHealthDrawer still consume them.
 */

export const MAINTENANCE_TYPE_LABELS = {
  oil_change: 'Oil Change',
  engine_inspection: 'Engine Inspection',
  spark_plug_service: 'Spark Plug Service',
  brake_pad_replacement: 'Brake Pad Replacement',
  brake_fluid_service: 'Brake Fluid Service',
  brake_inspection: 'Brake Inspection',
  coolant_flush: 'Coolant Flush',
  cooling_system_inspection: 'Cooling System Inspection',
  radiator_inspection: 'Radiator Inspection',
  transmission_service: 'Transmission Service',
  transmission_inspection: 'Transmission Inspection',
  fuel_filter_replacement: 'Fuel Filter Replacement',
  injector_cleaning: 'Injector Cleaning',
  fuel_pump_inspection: 'Fuel Pump Inspection',
  tire_replacement: 'Tire Replacement',
  other: 'Other Service',
};

export const MAINTENANCE_STATUS_META = {
  overdue: { label: 'Overdue', color: 'var(--color-red)', bg: 'var(--color-red-bg)' },
  dueSoon: { label: 'Due Soon', color: 'var(--color-amber)', bg: 'var(--color-amber-bg)' },
  scheduled: { label: 'Scheduled', color: 'var(--color-accent)', bg: 'var(--color-accent-subtle)' },
  future: { label: 'Future', color: 'var(--color-green)', bg: 'var(--color-green-bg)' },
};

export const MAINTENANCE_PRIORITY_META = {
  critical: { label: 'Critical', color: 'var(--color-red)', bg: 'var(--color-red-bg)' },
  high: { label: 'High', color: 'var(--color-amber)', bg: 'var(--color-amber-bg)' },
  medium: { label: 'Medium', color: 'var(--color-accent)', bg: 'var(--color-accent-subtle)' },
  low: { label: 'Low', color: 'var(--color-green)', bg: 'var(--color-green-bg)' },
};

const PRIORITY_RANK = { critical: 0, high: 1, medium: 2, low: 3 };
const STATUS_RANK = { overdue: 0, dueSoon: 1, scheduled: 2, future: 3 };

function titleCase(value) {
  if (!value) return 'Service';
  return String(value).replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

export function maintenanceTypeLabel(type) {
  return MAINTENANCE_TYPE_LABELS[type] || titleCase(type);
}

/**
 * Legacy helper, kept for VehicleDrawer / VehicleHealthDrawer.
 * Returns the uppercase legacy vocabulary: OVERDUE / DUE SOON /
 * SCHEDULED / GOOD.
 */
export function dueStatus(remainingKm) {
  if (remainingKm <= 0) return 'OVERDUE';
  if (remainingKm <= 500) return 'DUE SOON';
  if (remainingKm <= 2000) return 'SCHEDULED';
  return 'GOOD';
}

export function dueStatusStyle(status) {
  switch (status) {
    case 'OVERDUE': return { color: 'var(--color-red)', bg: 'var(--color-red-bg)' };
    case 'DUE SOON': return { color: 'var(--color-amber)', bg: 'var(--color-amber-bg)' };
    case 'SCHEDULED': return { color: 'var(--color-accent)', bg: 'var(--color-accent-subtle)' };
    case 'GOOD': return { color: 'var(--color-green)', bg: 'var(--color-green-bg)' };
    default: return { color: 'var(--color-text-muted)', bg: 'var(--color-surface-hover)' };
  }
}

/**
 * The single maintenance status vocabulary. Status is distance-first
 * (remaining km against the due odometer); when the odometer is unknown it
 * falls back to the scheduled due date. Returns one of the canonical keys
 * overdue | dueSoon | scheduled | future.
 */
export function computeMaintenanceStatus(remainingKm, record = {}) {
  if (remainingKm == null || !Number.isFinite(remainingKm)) {
    const dueMs = record.due_date ? new Date(record.due_date).getTime() : null;
    if (dueMs != null && Number.isFinite(dueMs)) {
      const daysLeft = (dueMs - Date.now()) / 86400000;
      if (daysLeft <= 0) return { key: 'overdue' };
      if (daysLeft <= 7) return { key: 'dueSoon' };
      if (daysLeft <= 30) return { key: 'scheduled' };
      return { key: 'future' };
    }
    return { key: 'future' };
  }
  if (remainingKm <= 0) return { key: 'overdue' };
  if (remainingKm <= 500) return { key: 'dueSoon' };
  if (remainingKm <= 2000) return { key: 'scheduled' };
  return { key: 'future' };
}

/**
 * Adapt raw backend records to rows the page can render directly. Joins
 * fleet meta (vehicle name, driver, odometer, health). ``remaining_km`` is
 * the signed distance to the due odometer (negative = already overdue).
 */
export function normalizeMaintenanceRecords(records, fleetMeta) {
  if (!Array.isArray(records)) return [];
  return records.map((record) => {
    const meta = fleetMeta?.[record.vehicle_id] || {};
    const odometerKm = Number.isFinite(meta.odometer_km) ? meta.odometer_km : null;
    const dueOdometerKm = Number.isFinite(record.due_odometer_km)
      ? record.due_odometer_km
      : null;
    const remainingKm =
      dueOdometerKm != null && odometerKm != null
        ? dueOdometerKm - odometerKm
        : null;
    const status = computeMaintenanceStatus(remainingKm, record);
    return {
      ...record,
      vehicle_name: meta.vehicle_name || record.vehicle_id,
      driver_name: meta.driver_name || null,
      odometer_km: odometerKm,
      remaining_km: remainingKm,
      overall_health_score: Number.isFinite(meta.overall_health_score)
        ? meta.overall_health_score
        : null,
      overall_health_status: meta.overall_health_status || null,
      maintenanceTypeLabel: maintenanceTypeLabel(record.maintenance_type),
      dueStatus: status.key,
      dueStatusLabel: MAINTENANCE_STATUS_META[status.key].label,
    };
  });
}

/**
 * Collapse records into canonical work items keyed by
 * (vehicle_id, maintenance_type). If the backend ever returns duplicate
 * projections for the same key, they are merged and the count is disclosed
 * via ``projectionCount`` (the page shows "N projections") instead of being
 * silently hidden.
 */
export function groupMaintenanceWorkItems(records) {
  if (!Array.isArray(records)) return [];
  const byKey = new Map();
  for (const record of records) {
    const key = `${record.vehicle_id}::${record.maintenance_type}`;
    const existing = byKey.get(key);
    if (existing) {
      existing.projectionCount += 1;
      existing.projections.push(record);
    } else {
      byKey.set(key, {
        ...record,
        workKey: key,
        projectionCount: 1,
        projections: [record],
      });
    }
  }
  return Array.from(byKey.values());
}

export function computeMaintenanceKpis(workItems) {
  const list = Array.isArray(workItems) ? workItems : [];
  const overdue = list.filter((w) => w.dueStatus === 'overdue').length;
  const dueSoon = list.filter((w) => w.dueStatus === 'dueSoon').length;
  const actionable = (w) =>
    w.dueStatus === 'overdue' || w.dueStatus === 'dueSoon' || w.dueStatus === 'scheduled';
  const dueWithin2000 = list.filter(actionable).length;
  const vehiclesRequiringService = new Set(
    list.filter(actionable).map((w) => w.vehicle_id)
  ).size;
  return {
    overdue,
    dueSoon,
    dueWithin2000,
    vehiclesRequiringService,
    total: list.length,
  };
}

export function computeVehicleMaintenanceRisk(workItems, fleetMeta) {
  const list = Array.isArray(workItems) ? workItems : [];
  const byVehicle = new Map();
  for (const item of list) {
    const arr = byVehicle.get(item.vehicle_id) || [];
    arr.push(item);
    byVehicle.set(item.vehicle_id, arr);
  }

  const rows = [];
  for (const [vehicleId, items] of byVehicle) {
    const meta = fleetMeta?.[vehicleId] || {};
    const counts = { overdue: 0, dueSoon: 0, scheduled: 0, future: 0 };
    for (const item of items) counts[item.dueStatus] += 1;
    const actionable = counts.overdue + counts.dueSoon + counts.scheduled;
    let level = 'good';
    if (counts.overdue > 0) level = 'critical';
    else if (counts.dueSoon > 0) level = 'high';
    else if (counts.scheduled > 0) level = 'medium';
    rows.push({
      vehicle_id: vehicleId,
      vehicle_name: meta.vehicle_name || vehicleId,
      driver_name: meta.driver_name || null,
      overall_health_score: Number.isFinite(meta.overall_health_score)
        ? meta.overall_health_score
        : null,
      overall_health_status: meta.overall_health_status || null,
      overdue: counts.overdue,
      dueSoon: counts.dueSoon,
      scheduled: counts.scheduled,
      future: counts.future,
      actionable,
      total: items.length,
      level,
    });
  }

  rows.sort(
    (a, b) =>
      PRIORITY_RANK_DANGER[a.level] - PRIORITY_RANK_DANGER[b.level] ||
      b.actionable - a.actionable ||
      a.vehicle_id.localeCompare(b.vehicle_id)
  );
  return rows;
}

const PRIORITY_RANK_DANGER = { critical: 0, high: 1, medium: 2, good: 3 };

export function computeServiceWorkload(workItems) {
  const list = Array.isArray(workItems) ? workItems : [];
  const byType = new Map();
  for (const item of list) {
    const entry = byType.get(item.maintenance_type) || {
      maintenance_type: item.maintenance_type,
      label: item.maintenanceTypeLabel,
      total: 0,
      overdue: 0,
      dueSoon: 0,
      scheduled: 0,
      future: 0,
    };
    entry.total += 1;
    entry[item.dueStatus] += 1;
    byType.set(item.maintenance_type, entry);
  }
  return Array.from(byType.values()).sort((a, b) => b.total - a.total);
}

const HORIZON_BUCKETS = [
  { key: 'overdue', label: 'Overdue', from: -Infinity, to: 0 },
  { key: 'week', label: 'This week', from: 0, to: 7 },
  { key: 'twoWeeks', label: 'Next 2 weeks', from: 7, to: 14 },
  { key: 'month', label: 'This month', from: 14, to: 30 },
  { key: 'later', label: 'Later', from: 30, to: Infinity },
];

/**
 * Workload over time, built only from rows that carry a real due_date.
 * Returns null when no due dates exist so callers can hide the panel
 * instead of drawing an invented schedule.
 */
export function computeMaintenanceHorizon(workItems, now = Date.now()) {
  const list = Array.isArray(workItems) ? workItems : [];
  const dated = list
    .map((item) => ({
      ...item,
      dueMs: item.due_date ? new Date(item.due_date).getTime() : null,
    }))
    .filter((item) => item.dueMs != null && Number.isFinite(item.dueMs));
  if (dated.length === 0) return null;

  const buckets = HORIZON_BUCKETS.map((b) => ({ ...b, count: 0 }));
  for (const item of dated) {
    const daysLeft = (item.dueMs - now) / 86400000;
    const bucket = buckets.find((b) => daysLeft >= b.from && daysLeft < b.to);
    if (bucket) bucket.count += 1;
  }
  return {
    total: dated.length,
    coverage: dated.length / list.length,
    buckets,
  };
}

export function computeMaintenanceInsights(workItems, vehicleRisk) {
  const list = Array.isArray(workItems) ? workItems : [];
  const insights = [];
  if (list.length === 0) return insights;

  const overdueItems = list.filter((w) => w.dueStatus === 'overdue');
  if (overdueItems.length > 0) {
    insights.push({
      key: 'overdue-work',
      kind: 'warning',
      title: `${overdueItems.length} work item${overdueItems.length === 1 ? ' is' : 's are'} overdue`,
      body: `${overdueItems.length} service${overdueItems.length === 1 ? '' : 's'} passed their due odometer or date. Schedule service before the next trip.`,
    });
  }

  const risk = Array.isArray(vehicleRisk) ? vehicleRisk : [];
  const converged = risk.filter(
    (r) => r.actionable >= 2 && (r.overdue > 0 || r.dueSoon > 0)
  );
  if (converged.length > 0) {
    insights.push({
      key: 'convergence',
      kind: 'warning',
      title: `${converged.length} vehicle${converged.length === 1 ? '' : 's'} have converging service windows`,
      body: converged
        .map((r) => `${r.vehicle_name} (${r.actionable} items)`)
        .join(' · '),
    });
  }

  const lowHealthImminent = risk.filter(
    (r) =>
      r.overall_health_score != null &&
      r.overall_health_score < 70 &&
      r.actionable > 0
  );
  if (lowHealthImminent.length > 0) {
    insights.push({
      key: 'low-health',
      kind: 'warning',
      title: `${lowHealthImminent.length} vehicle${lowHealthImminent.length === 1 ? '' : 's'} have low health with service due`,
      body: lowHealthImminent
        .map((r) => `${r.vehicle_name} (${Math.round(r.overall_health_score)} health)`)
        .join(' · '),
    });
  }

  const workload = computeServiceWorkload(list);
  const topType = workload[0];
  if (topType) {
    const immediate = topType.overdue + topType.dueSoon;
    insights.push({
      key: 'workload',
      kind: 'info',
      title: `${topType.label} is the most common service`,
      body: `${topType.total} work item${topType.total === 1 ? '' : 's'} across the fleet${immediate > 0 ? `, ${immediate} due immediately` : ''}.`,
    });
  }

  return insights;
}

export function filterMaintenanceWorkItems(items, filters) {
  let result = Array.isArray(items) ? items : [];
  const statusTab = filters?.statusTab || 'all';
  if (statusTab !== 'all') {
    result = result.filter((w) => w.dueStatus === statusTab);
  }
  if (filters?.dueWithin2000) {
    result = result.filter(
      (w) =>
        w.dueStatus === 'overdue' ||
        w.dueStatus === 'dueSoon' ||
        w.dueStatus === 'scheduled'
    );
  }
  const priority = filters?.priority || 'all';
  if (priority !== 'all') {
    result = result.filter((w) => w.priority === priority);
  }
  const type = filters?.type || 'all';
  if (type !== 'all') {
    result = result.filter((w) => w.maintenance_type === type);
  }
  const vehicleSearch = (filters?.vehicleSearch || '').trim().toLowerCase();
  if (vehicleSearch) {
    result = result.filter(
      (w) =>
        w.vehicle_name?.toLowerCase().includes(vehicleSearch) ||
        w.vehicle_id?.toLowerCase().includes(vehicleSearch)
    );
  }
  const driverSearch = (filters?.driverSearch || '').trim().toLowerCase();
  if (driverSearch) {
    result = result.filter((w) =>
      w.driver_name?.toLowerCase().includes(driverSearch)
    );
  }
  return result;
}

export function sortMaintenanceWorkItems(items, sortBy = 'status') {
  const list = [...(Array.isArray(items) ? items : [])];
  switch (sortBy) {
    case 'priority':
      return list.sort(
        (a, b) =>
          PRIORITY_RANK[a.priority] - PRIORITY_RANK[b.priority] ||
          STATUS_RANK[a.dueStatus] - STATUS_RANK[b.dueStatus]
      );
    case 'remaining':
      return list.sort(
        (a, b) => (a.remaining_km ?? Infinity) - (b.remaining_km ?? Infinity)
      );
    case 'vehicle':
      return list.sort(
        (a, b) =>
          a.vehicle_name.localeCompare(b.vehicle_name) ||
          STATUS_RANK[a.dueStatus] - STATUS_RANK[b.dueStatus]
      );
    case 'status':
    default:
      return list.sort(
        (a, b) =>
          STATUS_RANK[a.dueStatus] - STATUS_RANK[b.dueStatus] ||
          PRIORITY_RANK[a.priority] - PRIORITY_RANK[b.priority]
      );
  }
}

/**
 * Human-readable due display for a work item: remaining km when known,
 * else the scheduled due date, else a dash. Never invents a date.
 */
export function formatMaintenanceDue(item) {
  if (item && item.remaining_km != null && Number.isFinite(item.remaining_km)) {
    if (item.remaining_km <= 0) {
      const over = Math.abs(item.remaining_km);
      return over > 0 ? `Overdue by ${over.toLocaleString()} km` : 'Due now';
    }
    return `${item.remaining_km.toLocaleString()} km`;
  }
  if (item && item.due_date) {
    const d = new Date(item.due_date);
    if (!Number.isNaN(d.getTime())) {
      return d.toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' });
    }
  }
  return '\u2014';
}

/**
 * Completed service history — real completed records only, newest first.
 * Includes a name lookup so the drawer and history table can render
 * vehicle names without fabricating anything.
 */
export function sortMaintenanceHistory(records, fleetMeta) {
  const list = Array.isArray(records) ? records : [];
  return list
    .filter((r) => r.status === 'completed')
    .map((r) => ({
      ...r,
      vehicle_name: fleetMeta?.[r.vehicle_id]?.vehicle_name || r.vehicle_id,
      maintenanceTypeLabel: maintenanceTypeLabel(r.maintenance_type),
    }))
    .sort(
      (a, b) =>
        (new Date(b.completed_at || b.created_at || 0).getTime() || 0) -
        (new Date(a.completed_at || a.created_at || 0).getTime() || 0)
    );
}
