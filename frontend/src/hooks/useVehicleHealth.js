import { useMemo } from 'react';
import { useLiveData } from '../context/LiveDataContext';
import { computeComponentHealth, healthCategory } from '../utils/health';

function clamp(value) {
  const n = Number(value);
  if (!Number.isFinite(n)) return 100;
  return Math.max(0, Math.min(100, Math.round(n)));
}

function average(a, b) {
  const x = Number(a);
  const y = Number(b);
  const nums = [x, y].filter((n) => Number.isFinite(n));
  if (nums.length === 0) return 100;
  return nums.reduce((sum, n) => sum + n, 0) / nums.length;
}

function mapComponentHealth(record) {
  if (!record) return null;
  return {
    engine: clamp(record.engine_health),
    braking: clamp(record.brake_health),
    fuel: clamp(record.fuel_system_health),
    behaviour: clamp(average(record.transmission_health, record.cooling_health)),
  };
}

function mapVehicle(v, healthRecord) {
  const restComponents = mapComponentHealth(healthRecord);
  const liveComponents = computeComponentHealth({
    coolantTemp: v.coolant_temperature_c ?? 0,
    engineLoad: v.engine_load_percent ?? 0,
    harshBraking: v.harsh_braking ?? false,
    brakePressure: v.brake_percent ?? 0,
    fuelLevel: v.fuel_level_percent ?? 0,
    aggressiveThrottle: v.aggressive_throttle ?? false,
    speeding: v.speeding ?? false,
    highRpm: v.high_rpm ?? false,
  });

  const overall = v.overall_health_score ?? healthRecord?.overall_health_score ?? 100;
  const components = {
    engine: restComponents?.engine ?? liveComponents.engine,
    braking: restComponents?.braking ?? liveComponents.braking,
    fuel: restComponents?.fuel ?? liveComponents.fuel,
    behaviour: restComponents?.behaviour ?? liveComponents.behaviour,
  };

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
    brakePressure: v.brake_percent ?? 0,
    activeEvents: v.active_event_types || [],
    speeding: !!v.speeding,
    harshBraking: !!v.harsh_braking,
    aggressiveThrottle: !!v.aggressive_throttle,
    highRpm: !!v.high_rpm,
    lastUpdated: v.last_updated_at,
  };
}

export function useVehicleHealth() {
  const { mergedFleet, vehicleHealth } = useLiveData();

  return useMemo(() => {
    if (!Array.isArray(mergedFleet) || mergedFleet.length === 0) {
      return { vehicles: [], fleetStats: null };
    }

    const healthById = new Map((vehicleHealth || []).map((h) => [h.vehicle_id, h]));
    const vehicles = mergedFleet.map((v) => mapVehicle(v, healthById.get(v.vehicle_id)));

    const scores = vehicles.map((v) => v.overallHealth);
    const avgScore = Math.round(scores.reduce((a, b) => a + b, 0) / scores.length);

    const healthyCount = vehicles.filter((v) => v.healthCategory === 'healthy').length;
    const warningCount = vehicles.filter((v) => v.healthCategory === 'warning').length;
    const criticalCount = vehicles.filter((v) => v.healthCategory === 'critical').length;

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
  }, [mergedFleet, vehicleHealth]);
}

export function useVehicle(vehicleId) {
  const { vehicles } = useVehicleHealth();
  return useMemo(() => vehicles.find((v) => v.id === vehicleId) || null, [vehicles, vehicleId]);
}
