import { useMemo } from 'react';
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

function formatRelative(iso) {
  if (!iso) return 'Just now';
  const diff = Date.now() - new Date(iso).getTime();
  const sec = Math.floor(diff / 1000);
  if (sec < 60) return 'Just now';
  const min = Math.floor(sec / 60);
  if (min < 60) return `${min} min ago`;
  const hr = Math.floor(min / 60);
  return `${hr} hour${hr > 1 ? 's' : ''} ago`;
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

export function useVehicles() {
  const { dashboard } = useFleetContext();
  return useMemo(() => {
    const mapped = mapVehicles(dashboard?.vehicles);
    return mapped || fleetService.getVehicles();
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

  if (!dashboard) {
    return {
      totalVehicles: 0,
      activeVehicles: 0,
      fleetHealthScore: 0,
      attentionRequired: 0,
    };
  }

  return {
    totalVehicles: dashboard.total_fleet ?? 0,
    activeVehicles: dashboard.active_vehicle_count ?? 0,
    fleetHealthScore: dashboard.fleet_health_score ?? 0,
    attentionRequired: dashboard.attention_required ?? 0,
  };
}

export function useTelemetryData() {
  return useMemo(() => fleetService.getTelemetryData(), []);
}

export function useUnacknowledgedAlertCount() {
  return useMemo(() => fleetService.getUnacknowledgedAlertCount(), []);
}
