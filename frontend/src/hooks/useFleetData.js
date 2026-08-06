import { useMemo } from 'react';
import { useLiveData } from '../context/LiveDataContext';

function mapStatus(s) {
  if (s === 'ACTIVE') return 'active';
  if (s === 'IDLE') return 'idle';
  if (s === 'TRIP COMPLETED') return 'trip_completed';
  return 'offline';
}

function healthCategory(score) {
  if (score == null) return 'healthy';
  if (score >= 85) return 'healthy';
  if (score >= 70) return 'monitor';
  if (score >= 50) return 'attention';
  return 'critical';
}

const DISPLAY_STATUS_DEBOUNCE_MS = 2000;
const _statusMemory = new Map();

function computeRawDisplayStatus(v) {
  if (v.activeEventTypes && v.activeEventTypes.length > 0) return 'ALERT';
  if (v.maintenanceDue) return 'MAINTENANCE';
  if (v.status === 'active') return 'ACTIVE';
  if (v.status === 'trip_completed') return 'TRIP_COMPLETED';
  if (v.status === 'idle') return 'IDLE';
  return 'OFFLINE';
}

function resolveDisplayStatus(vehicleId, raw, now) {
  const prev = _statusMemory.get(vehicleId);
  if (!prev) {
    _statusMemory.set(vehicleId, { current: raw, target: raw, since: now });
    return raw;
  }
  if (prev.target === raw) {
    if (prev.current !== raw && now - prev.since >= DISPLAY_STATUS_DEBOUNCE_MS) {
      prev.current = raw;
    }
    return prev.current;
  }
  prev.target = raw;
  prev.since = now;
  return prev.current;
}

function mapVehicles(raw) {
  if (!raw || !Array.isArray(raw)) return null;
  return raw.map((v) => ({
    id: v.vehicle_id,
    name: v.vehicle_name || v.vehicle_id,
    driver: v.driver_name || v.driver_id || '—',
    driverId: v.driver_id,
    status: mapStatus(v.operational_status),
    tripStatus: v.trip_status || 'active',
    maintenanceDue: !!v.maintenance_due,
    speed: v.speed_kmh ?? 0,
    rpm: v.rpm ?? 0,
    throttle: v.throttle_position_percent ?? null,
    brake: v.brake_pressure ?? null,
    fuelLevel: v.fuel_level_percent ?? 0,
    coolantTemp: v.coolant_temperature_c ?? 0,
    engineLoad: v.engine_load_percent ?? null,
    healthScore: v.overall_health_score ?? 0,
    healthCategory: healthCategory(v.overall_health_score),
    odometer: v.odometer_km ?? 0,
    lastUpdate: v.last_updated_at,
    alertCount: v.active_alert_count ?? 0,
    activeAlert: v.active_alert_text || null,
    activeEventTypes: v.active_event_types || [],
    speeding: v.speeding ?? false,
    aggressiveThrottle: v.aggressive_throttle ?? false,
    harshBraking: v.harsh_braking ?? false,
    highRpm: v.high_rpm ?? false,
  }));
}

let _stableCache = null;

function shallowEqual(a, b) {
  if (a === b) return true;
  if (!a || !b) return false;
  const ka = Object.keys(a), kb = Object.keys(b);
  if (ka.length !== kb.length) return false;
  for (const k of ka) if (a[k] !== b[k]) return false;
  return true;
}

function stableVehicles(raw) {
  const mapped = mapVehicles(raw);
  if (!mapped) return null;
  const now = Date.now();
  for (const v of mapped) {
    v.displayStatus = resolveDisplayStatus(v.id, computeRawDisplayStatus(v), now);
  }
  if (_stableCache && _stableCache.length === mapped.length) {
    let changed = false;
    for (let i = 0; i < mapped.length; i++) {
      if (!shallowEqual(mapped[i], _stableCache[i])) { changed = true; break; }
    }
    if (!changed) return _stableCache;
  }
  _stableCache = mapped;
  return mapped;
}

export function useVehicles() {
  const { mergedFleet } = useLiveData();
  return useMemo(() => stableVehicles(mergedFleet) || [], [mergedFleet]);
}

export function useVehicle(id) {
  const vehicles = useVehicles();
  return useMemo(() => vehicles.find((v) => v.id === id), [vehicles, id]);
}

function computeSummaryFallback(mergedFleet) {
  if (!mergedFleet || mergedFleet.length === 0) {
    return { totalVehicles: 0, activeVehicles: 0, fleetHealthScore: 0, attentionRequired: 0 };
  }
  const scores = mergedFleet
    .map((v) => v.overall_health_score)
    .filter((s) => s != null);
  const avgScore = scores.length > 0
    ? Math.round(scores.reduce((sum, s) => sum + s, 0) / scores.length)
    : 0;
  return {
    totalVehicles: mergedFleet.length,
    activeVehicles: mergedFleet.filter((v) => v.operational_status === 'ACTIVE').length,
    fleetHealthScore: avgScore,
    attentionRequired: mergedFleet.filter((v) => (v.active_alert_count ?? 0) > 0).length,
  };
}

export function useDashboardSummary() {
  const { dashboard, mergedFleet } = useLiveData();
  return useMemo(() => {
    if (dashboard) {
      return {
        totalVehicles: dashboard.total_fleet ?? 0,
        activeVehicles: dashboard.active_vehicle_count ?? 0,
        fleetHealthScore: Math.round(dashboard.fleet_health_score ?? 0),
        attentionRequired: dashboard.attention_required ?? 0,
      };
    }
    return computeSummaryFallback(mergedFleet);
  }, [dashboard, mergedFleet]);
}

function formatTime(iso) {
  if (!iso) return null;
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return null;
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
}

function telemetrySafety(t) {
  let score = 100;
  if ((t.engine_load_percent ?? 0) > 85) score -= 15;
  if ((t.coolant_temperature_c ?? 0) > 105) score -= 20;
  else if ((t.coolant_temperature_c ?? 0) > 95) score -= 10;
  if ((t.fuel_level_percent ?? 100) < 15) score -= 15;
  if ((t.brake_percent ?? 0) > 0.7) score -= 8;
  if ((t.throttle_percent ?? 0) > 85) score -= 8;
  return Math.max(0, Math.min(100, Math.round(score)));
}

export function useTelemetryData() {
  const { telemetry } = useLiveData();
  return useMemo(() => {
    if (!Array.isArray(telemetry) || telemetry.length === 0) return [];
    const byTime = new Map();
    for (const t of telemetry) {
      const time = formatTime(t.timestamp);
      if (!time) continue;
      const fuelRate = t.fuel_rate_lph ?? 0;
      const speed = t.speed_kmh ?? 0;
      const fuelEfficiency = fuelRate > 0 ? Math.round((speed / fuelRate) * 100) / 100 : 0;
      byTime.set(time, { time, fuelEfficiency, safetyScore: telemetrySafety(t) });
    }
    return [...byTime.values()]
      .sort((a, b) => a.time.localeCompare(b.time))
      .slice(-12);
  }, [telemetry]);
}

const MAINTENANCE_TYPE_LABELS = {
  oil_change: 'Oil Change',
  brake_inspection: 'Brake Inspection',
  tyre_rotation: 'Tyre Rotation',
  coolant: 'Coolant',
  general_inspection: 'General Inspection',
};

function titleCase(value) {
  if (!value) return 'Service';
  return String(value).replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

function mapMaintenanceQueueItem(item, meta) {
  const odometer = meta?.odometer_km ?? 0;
  const due = item.due_odometer_km;
  const dueDistance = due != null ? Math.max(0, Math.round(due - odometer)) : undefined;
  const overdue = due != null && dueDistance === 0;
  const priority =
    item.priority === 'critical' || overdue ? 'critical' :
    item.priority === 'high' || item.priority === 'medium' ? 'upcoming' :
    'monitor';
  return {
    id: item.maintenance_id,
    vehicleId: item.vehicle_id,
    type: MAINTENANCE_TYPE_LABELS[item.maintenance_type] || titleCase(item.maintenance_type),
    priority,
    dueDistance,
    dueDate: due == null ? item.created_at : undefined,
    description: due != null ? `Due at ${Math.round(due).toLocaleString()} km` : 'Service required',
  };
}

export function useMaintenanceItems() {
  const { maintenance, fleetMeta } = useLiveData();
  return useMemo(() => {
    if (!Array.isArray(maintenance)) return [];
    const order = { critical: 0, upcoming: 1, monitor: 2 };
    return maintenance
      .map((item) => mapMaintenanceQueueItem(item, fleetMeta?.[item.vehicle_id]))
      .sort((a, b) => order[a.priority] - order[b.priority]);
  }, [maintenance, fleetMeta]);
}

export function useUnacknowledgedAlertCount() {
  const { alerts } = useLiveData();
  return useMemo(() => {
    if (!Array.isArray(alerts)) return 0;
    return alerts.filter((a) => !a.acknowledged).length;
  }, [alerts]);
}

const LEGACY_ALERT_TITLES = {
  engine_overheat: 'Engine coolant overheat',
  coolant_warning: 'Elevated coolant temperature',
  fuel_critical: 'Fuel level critical',
  low_fuel: 'Low fuel level',
  health_critical: 'Vehicle health critical',
  health_warning: 'Vehicle health warning',
  high_engine_load: 'High engine load',
  harsh_braking: 'Repeated harsh braking',
  aggressive_throttle: 'Aggressive throttle use',
  high_rpm: 'Excessive engine RPM',
  speeding: 'Speeding detected',
};

function normalizeSeverity(sev) {
  const s = String(sev || 'warning').toLowerCase();
  if (s === 'critical' || s === 'warning' || s === 'info') return s;
  return 'warning';
}

function relativeTime(iso) {
  if (!iso) return '—';
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return '—';
  const mins = Math.max(0, Math.round((Date.now() - then) / 60000));
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins} minute${mins === 1 ? '' : 's'} ago`;
  const hrs = Math.round(mins / 60);
  if (hrs < 24) return `${hrs} hour${hrs === 1 ? '' : 's'} ago`;
  const days = Math.round(hrs / 24);
  return `${days} day${days === 1 ? '' : 's'} ago`;
}

function mapLegacyAlert(a, meta) {
  return {
    id: a.alert_id,
    severity: normalizeSeverity(a.severity),
    vehicleId: a.vehicle_id,
    vehicleName: meta?.vehicle_name || a.vehicle_id,
    driverId: a.driver_id,
    driverName: meta?.driver_name || '—',
    title: LEGACY_ALERT_TITLES[a.alert_type] || titleCase(a.alert_type),
    description: 'Active alert requiring review.',
    value: null,
    threshold: null,
    timestamp: relativeTime(a.created_at),
    createdAt: a.created_at,
    acknowledged: !!a.acknowledged,
    status: a.status === 'resolved' ? 'resolved' : 'active',
    resolvedAt: a.resolved_at || null,
    actionLabel: 'View Vehicle',
  };
}

export function useAlerts() {
  const { alerts, fleetMeta } = useLiveData();
  return useMemo(() => {
    if (!Array.isArray(alerts)) return [];
    return alerts.map((a) => mapLegacyAlert(a, fleetMeta?.[a.vehicle_id]));
  }, [alerts, fleetMeta]);
}
