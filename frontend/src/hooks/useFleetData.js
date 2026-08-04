import { useMemo, useRef } from 'react';
import * as fleetService from '../services/fleetService';
import { useFleetContext } from '../context/FleetContext';

function mapStatus(s) {
  if (s === 'ACTIVE') return 'active';
  if (s === 'IDLE') return 'idle';
  return 'offline';
}

function healthCategory(score) {
  if (score == null) return 'healthy';
  if (score >= 85) return 'healthy';
  if (score >= 70) return 'monitor';
  if (score >= 50) return 'attention';
  return 'critical';
}

function mapVehicles(raw) {
  if (!raw || !Array.isArray(raw)) return null;
  return raw.map((v) => ({
    id: v.vehicle_id,
    name: v.vehicle_name || v.vehicle_id,
    driver: v.driver_name || v.driver_id || '—',
    driverId: v.driver_id,
    status: mapStatus(v.operational_status),
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
  const { dashboard } = useFleetContext();
  const fallbackRef = useRef(null);
  return useMemo(() => {
    const stable = stableVehicles(dashboard?.vehicles);
    if (stable) return stable;
    if (!fallbackRef.current) fallbackRef.current = fleetService.getVehicles();
    return fallbackRef.current;
  }, [dashboard]);
}

export function useVehicle(id) {
  const vehicles = useVehicles();
  return useMemo(() => vehicles.find((v) => v.id === id), [vehicles, id]);
}

export function useDrivers() {
  return useMemo(() => fleetService.getDrivers(), []);
}

export function useTopDrivers(count) {
  return useMemo(() => fleetService.getTopDrivers(count), [count]);
}

export function useAlerts() {
  return useMemo(() => fleetService.getAlerts(), []);
}

export function useMaintenanceItems() {
  return useMemo(() => fleetService.getMaintenanceItems(), []);
}

export function useDashboardSummary() {
  const { dashboard } = useFleetContext();
  return useMemo(() => ({
    totalVehicles: dashboard?.total_fleet ?? 0,
    activeVehicles: dashboard?.active_vehicle_count ?? 0,
    fleetHealthScore: dashboard?.fleet_health_score ?? 0,
    attentionRequired: dashboard?.attention_required ?? 0,
  }), [dashboard]);
}

export function useTelemetryData() {
  return useMemo(() => fleetService.getTelemetryData(), []);
}

export function useUnacknowledgedAlertCount() {
  return useMemo(() => fleetService.getUnacknowledgedAlertCount(), []);
}
