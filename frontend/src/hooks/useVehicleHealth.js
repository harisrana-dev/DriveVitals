import { useMemo } from 'react';
import { useLiveData } from '../context/useLiveData';
import { canonicalHealthCategory } from '../utils/health';

const COMPONENT_KEYS = ['engine', 'cooling', 'braking', 'transmission', 'fuel'];

function subsystemScore(v, key) {
  switch (key) {
    case 'engine': return v.engine_health ?? null;
    case 'cooling': return v.cooling_health ?? null;
    case 'braking': return v.brake_health ?? null;
    case 'transmission': return v.transmission_health ?? null;
    case 'fuel': return v.fuel_system_health ?? null;
    default: return null;
  }
}

function subsystemStatus(v, key) {
  switch (key) {
    case 'engine': return v.engine_health_status ?? null;
    case 'cooling': return v.cooling_health_status ?? null;
    case 'braking': return v.brake_health_status ?? null;
    case 'transmission': return v.transmission_health_status ?? null;
    case 'fuel': return v.fuel_system_health_status ?? null;
    default: return null;
  }
}

function mapVehicle(v) {
  const overallHealth = v.overall_health_score ?? null;
  const healthStatus = v.overall_health_status ?? null;

  const components = {};
  const componentsStatus = {};
  for (const key of COMPONENT_KEYS) {
    const score = subsystemScore(v, key);
    const status = subsystemStatus(v, key);
    components[key] = score;
    componentsStatus[key] = status;
  }

  return {
    id: v.vehicle_id,
    name: v.vehicle_name || v.vehicle_id,
    driverId: v.driver_id,
    driverName: v.driver_name || '\u2014',
    status: v.operational_status,
    overallHealth: overallHealth,
    healthStatus: healthStatus,
    healthCategory: canonicalHealthCategory(overallHealth, healthStatus),
    components,
    componentsStatus,
    healthReasons: v.health_reasons || [],
    speed: v.speed_kmh ?? null,
    rpm: v.rpm ?? null,
    fuelLevel: v.fuel_level_percent ?? null,
    coolantTemp: v.coolant_temperature_c ?? null,
    engineLoad: v.engine_load_percent ?? null,
    brakePressure: v.brake_percent ?? null,
    odometer: v.odometer_km ?? null,
    activeEvents: v.active_event_types || [],
    speeding: !!v.speeding,
    harshBraking: !!v.harsh_braking,
    aggressiveThrottle: !!v.aggressive_throttle,
    highRpm: !!v.high_rpm,
    lastUpdated: v.last_updated_at,
  };
}

export function useVehicleHealth() {
  const { mergedFleet } = useLiveData();

  return useMemo(() => {
    if (!Array.isArray(mergedFleet) || mergedFleet.length === 0) {
      return { vehicles: [], fleetStats: null };
    }

    const vehicles = mergedFleet.map(mapVehicle);

    const scores = vehicles
      .map((v) => v.overallHealth)
      .filter((s) => s != null);
    const avgScore = scores.length > 0
      ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length)
      : null;

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
  }, [mergedFleet]);
}

export function useVehicle(vehicleId) {
  const { vehicles } = useVehicleHealth();
  return useMemo(() => vehicles.find((v) => v.id === vehicleId) || null, [vehicles, vehicleId]);
}
