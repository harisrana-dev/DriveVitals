import { driverHistorical } from '../mocks/drivers';

function getInitials(name) {
  if (!name) return '--';
  return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
}

function mapStatus(opStatus) {
  if (opStatus === 'ACTIVE') return 'active';
  if (opStatus === 'IDLE') return 'off_duty';
  return 'offline';
}

function buildBehaviourEvents(v) {
  return {
    harshBraking: {
      count: v.harsh_braking ? 1 : 0,
      trend: 'stable',
      severity: v.harsh_braking ? 'moderate' : 'none',
      active: !!v.harsh_braking,
    },
    aggressiveAcceleration: {
      count: v.aggressive_throttle ? 1 : 0,
      trend: 'stable',
      severity: v.aggressive_throttle ? 'moderate' : 'none',
      active: !!v.aggressive_throttle,
    },
    overspeedEvents: {
      count: v.speeding ? 1 : 0,
      trend: 'stable',
      severity: v.speeding ? 'moderate' : 'none',
      active: !!v.speeding,
    },
    highRpmEvents: {
      count: v.high_rpm ? 1 : 0,
      trend: 'stable',
      severity: v.high_rpm ? 'moderate' : 'none',
      active: !!v.high_rpm,
    },
  };
}

function buildScoreBreakdown(score, v) {
  const b = {
    braking: score - (v.harsh_braking ? 15 : 0),
    acceleration: score - (v.aggressive_throttle ? 10 : 0),
    speed: score - (v.speeding ? 12 : 0),
    efficiency: Math.min(100, score + 5),
    overall: score,
  };
  for (const k of Object.keys(b)) {
    b[k] = Math.max(0, Math.min(100, Math.round(b[k])));
  }
  return b;
}

export function adaptVehicleToDriver(v) {
  const score = v.driver_safety_score ?? 100;
  const activeEvents = v.active_event_types || [];
  const hasBehaviour = activeEvents.length > 0;
  const hist = driverHistorical[v.driver_id] || {};

  const behaviour = buildBehaviourEvents(v);

  return {
    id: v.driver_id,
    name: v.driver_name || v.driver_id,
    initials: getInitials(v.driver_name),
    status: mapStatus(v.operational_status),
    riskLevel: v.driver_risk_level || 'low',
    behaviourState: hasBehaviour ? 'declining' : (hist.behaviourState || 'stable'),
    trend: hasBehaviour ? 'declining' : (hist.trend || 'stable'),
    vehicleId: v.vehicle_id,
    vehicleName: v.vehicle_name || v.vehicle_id,
    safetyScore: score,
    scoreBreakdown: buildScoreBreakdown(score, v),
    activeEventTypes: activeEvents,

    speed: v.speed_kmh,
    rpm: v.rpm,
    throttle: v.throttle_position_percent,
    brake: v.brake_pressure,
    fuelLevel: v.fuel_level_percent,
    engineLoad: v.engine_load_percent,
    coolantTemp: v.coolant_temperature_c,
    healthScore: v.overall_health_score,

    ...behaviour,
    lastActive: v.last_updated_at,

    totalDistanceKm: hist.totalDistanceKm ?? 0,
    tripsCompleted: hist.tripsCompleted ?? 0,
    averageSpeedKmh: hist.averageSpeedKmh ?? 0,
    fuelEfficiencyKmPerL: hist.fuelEfficiencyKmPerL ?? 0,
    drivingHours: hist.drivingHours ?? 0,
    tripsToday: hist.tripsToday ?? 0,
    performanceHistory: hist.performanceHistory ?? [],
    behaviourDistribution: hist.behaviourDistribution ?? { smoothDriving: 100, harshEvents: 0, overspeed: 0, idle: 0 },
  };
}

export function adaptVehiclesToDrivers(vehicles) {
  if (!vehicles || !Array.isArray(vehicles)) return [];
  return vehicles.map(adaptVehicleToDriver);
}

export function buildDriverRankings(drivers) {
  return [...drivers]
    .sort((a, b) => b.safetyScore - a.safetyScore)
    .map(d => ({
      id: d.id,
      name: d.name,
      score: d.safetyScore,
      tripsCompleted: d.tripsCompleted,
      trend: d.trend,
      scoreDelta: d.scoreDelta ?? 0,
      scoreTrend: d.scoreTrend ?? null,
    }));
}
