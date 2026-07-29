import { useMemo } from 'react';
import { useFleetContext } from '../context/FleetContext';
import { computeComponentHealth, healthCategory } from '../utils/health';

function mapVehicle(v) {
  const overall = v.overall_health_score ?? 100;
  const components = computeComponentHealth(v);
  return {
    id: v.vehicle_id,
    name: v.vehicle_name || v.vehicle_id,
    driverId: v.driver_id,
    driverName: v.driver_name || '\u2014',
    status: v.operational_status,
    overallHealth: overall,
    healthCategory: healthCategory(overall),
    components,
    speed: v.speed_kmh ?? 0,
    rpm: v.rpm ?? 0,
    fuelLevel: v.fuel_level_percent ?? 0,
    coolantTemp: v.coolant_temperature_c ?? 0,
    engineLoad: v.engine_load_percent ?? 0,
    brakePressure: v.brake_pressure ?? 0,
    activeEvents: v.active_event_types || [],
    speeding: !!v.speeding,
    harshBraking: !!v.harsh_braking,
    aggressiveThrottle: !!v.aggressive_throttle,
    highRpm: !!v.high_rpm,
    lastUpdated: v.last_updated_at,
  };
}

export function useVehicleHealth() {
  const { dashboard } = useFleetContext();

  return useMemo(() => {
    const raw = dashboard?.vehicles;
    if (!raw || !Array.isArray(raw) || raw.length === 0) {
      return { vehicles: [], fleetStats: null };
    }

    const vehicles = raw.map(mapVehicle);

    const scores = vehicles.map(v => v.overallHealth);
    const avgScore = Math.round(scores.reduce((a, b) => a + b, 0) / scores.length);

    const healthyCount = vehicles.filter(v => v.healthCategory === 'healthy').length;
    const warningCount = vehicles.filter(v => v.healthCategory === 'warning').length;
    const criticalCount = vehicles.filter(v => v.healthCategory === 'critical').length;

    return {
      vehicles,
      fleetStats: {
        total: vehicles.length,
        avgScore,
        healthyCount,
        warningCount,
        criticalCount,
      },
    };
  }, [dashboard]);
}

export function useVehicle(vehicleId) {
  const { vehicles } = useVehicleHealth();
  return useMemo(() => vehicles.find(v => v.id === vehicleId) || null, [vehicles, vehicleId]);
}
