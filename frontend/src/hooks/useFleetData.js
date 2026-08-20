import { useMemo } from 'react';
import { useLiveData } from '../context/useLiveData';
import { normalizeHealthReasons, canonicalHealthCategory } from '../utils/health';
import { useNow } from './useNow';

function mapStatus(s) {
  if (s === 'ACTIVE') return 'active';
  if (s === 'IDLE') return 'idle';
  if (s === 'TRIP COMPLETED') return 'trip_completed';
  return 'offline';
}

export const DISPLAY_STATUS_DEBOUNCE_MS = 2000;
const OFFLINE_AFTER_MS = 60000;
const _statusMemory = new Map();

function computeRawDisplayStatus(v, now) {
  const lastUpdate = v.lastUpdate ? new Date(v.lastUpdate).getTime() : 0;
  const stale = !lastUpdate || now - lastUpdate > OFFLINE_AFTER_MS;
  if (!lastUpdate) return 'OFFLINE';
  if (v.status === 'trip_completed') return 'TRIP_COMPLETED';
  if (v.status === 'active') return 'ACTIVE';
  if (v.status === 'idle') return stale ? 'STALE' : 'IDLE';
  if (stale) return 'STALE';
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
    speed: v.speed_kmh ?? null,
    rpm: v.rpm ?? null,
    throttle: v.throttle_position_percent ?? null,
    brake: v.brake_percent ?? null,
    fuelLevel: v.fuel_level_percent ?? null,
    coolantTemp: v.coolant_temperature_c ?? null,
    engineLoad: v.engine_load_percent ?? null,
    healthScore: v.overall_health_score ?? null,
    healthStatus: v.overall_health_status ?? null,
    healthCategory: canonicalHealthCategory(v.overall_health_score, v.overall_health_status),
    odometer: v.odometer_km ?? null,
    lastUpdate: v.last_updated_at,
    alertCount: v.active_alert_count ?? null,
    activeAlert: v.active_alert_text || null,
    activeEventTypes: v.active_event_types || [],
    reasons: normalizeHealthReasons(v.health_reasons || []),
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

function stableVehicles(raw, now) {
  const mapped = mapVehicles(raw);
  if (!mapped) return null;
  for (const v of mapped) {
    v.displayStatus = resolveDisplayStatus(v.id, computeRawDisplayStatus(v, now), now);
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
  const now = useNow(5000);
  return useMemo(() => stableVehicles(mergedFleet, now) || [], [mergedFleet, now]);
}

export function useVehicle(id) {
  const vehicles = useVehicles();
  return useMemo(() => vehicles.find((v) => v.id === id), [vehicles, id]);
}

function computeSummaryFallback(mergedFleet) {
  if (!mergedFleet || mergedFleet.length === 0) {
    return { totalVehicles: 0, activeVehicles: 0, fleetHealthScore: null, attentionRequired: 0 };
  }
  const scores = mergedFleet
    .map((v) => v.overall_health_score)
    .filter((s) => s != null);
  const avgScore = scores.length > 0
    ? Math.round(scores.reduce((sum, s) => sum + s, 0) / scores.length)
    : null;
  return {
    totalVehicles: mergedFleet.length,
    activeVehicles: mergedFleet.filter((v) => v.operational_status === 'ACTIVE' || v.operational_status === 'IDLE').length,
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
        fleetHealthScore:
          dashboard.fleet_health_score == null
            ? null
            : Math.round(dashboard.fleet_health_score),
        attentionRequired: dashboard.attention_required ?? 0,
      };
    }
    return computeSummaryFallback(mergedFleet);
  }, [dashboard, mergedFleet]);
}

/**
 * Open (active, unacknowledged) alert count for the top bar. Uses the
 * canonical "active && !acknowledged" definition so resolved rows are
 * never counted as requiring attention.
 */
export function useUnacknowledgedAlertCount() {
  const { alerts } = useLiveData();
  return useMemo(() => {
    if (!Array.isArray(alerts)) return 0;
    return alerts.filter((a) => a.status === 'active' && !a.acknowledged).length;
  }, [alerts]);
}
