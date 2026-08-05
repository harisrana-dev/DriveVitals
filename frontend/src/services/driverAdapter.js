function getInitials(name) {
  if (!name) return '--';
  return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
}

function mapStatus(opStatus) {
  if (opStatus === 'ACTIVE') return 'active';
  if (opStatus === 'IDLE') return 'off_duty';
  return 'offline';
}

function behaviourBlock(count, active) {
  const countValue = count > 0 ? count : active ? 1 : 0;
  return {
    count: countValue,
    trend: 'stable',
    severity: count >= 5 ? 'severe' : countValue > 0 ? 'moderate' : 'none',
    active: !!active,
  };
}

function buildBehaviourEvents(stats, live) {
  return {
    harshBraking: behaviourBlock(stats?.harsh_braking_events ?? 0, live?.harsh_braking),
    aggressiveAcceleration: behaviourBlock(stats?.aggressive_throttle_events ?? 0, live?.aggressive_throttle),
    overspeedEvents: behaviourBlock(stats?.speeding_events ?? 0, live?.speeding),
    highRpmEvents: behaviourBlock(stats?.high_rpm_events ?? 0, live?.high_rpm),
  };
}

function buildScoreBreakdown(stats) {
  const overall = stats?.safety_score ?? 100;
  const aggression = stats?.aggression_score ?? 100;
  const b = {
    braking: overall,
    acceleration: Math.max(0, Math.min(100, Math.round(overall - (100 - aggression) * 0.6))),
    speed: overall,
    efficiency: stats?.efficiency_score ?? 100,
    overall,
  };
  for (const k of Object.keys(b)) {
    b[k] = Math.max(0, Math.min(100, Math.round(b[k])));
  }
  return b;
}

function riskFor(score, aggression) {
  if (score == null) return 'low';
  if (score < 60 || (aggression != null && aggression < 60)) return 'critical';
  if (score < 75 || (aggression != null && aggression < 75)) return 'high';
  if (score < 85) return 'moderate';
  return 'low';
}

function buildBehaviourDistribution(stats) {
  const harsh = stats?.harsh_braking_events ?? 0;
  const overspeed = stats?.speeding_events ?? 0;
  const aggressive = stats?.aggressive_throttle_events ?? 0;
  const highRpm = stats?.high_rpm_events ?? 0;
  const eventTotal = harsh + overspeed + aggressive + highRpm;
  return {
    smoothDriving: Math.max(0, 100 - eventTotal * 5),
    harshEvents: harsh,
    overspeed,
    idle: 0,
  };
}

function adaptDriver(driver, stats, live) {
  const name = `${driver.first_name || ''} ${driver.last_name || ''}`.trim() || driver.driver_id;
  const score = stats?.safety_score ?? live?.driver_safety_score ?? 100;
  const activeEvents = live?.active_event_types || [];
  const behaviour = buildBehaviourEvents(stats, live);

  return {
    id: driver.driver_id,
    name,
    initials: getInitials(name),
    status: mapStatus(live?.operational_status),
    riskLevel: riskFor(score, stats?.aggression_score),
    behaviourState: activeEvents.length > 0 ? 'declining' : 'stable',
    trend: 'stable',
    vehicleId: live?.vehicle_id ?? null,
    vehicleName: live?.vehicle_name || null,
    safetyScore: Math.round(score),
    scoreBreakdown: buildScoreBreakdown(stats),
    activeEventTypes: activeEvents,

    speed: live?.speed_kmh ?? 0,
    rpm: live?.rpm ?? 0,
    throttle: live?.throttle_position_percent ?? 0,
    brake: live?.brake_pressure ?? 0,
    fuelLevel: live?.fuel_level_percent ?? 0,
    engineLoad: live?.engine_load_percent ?? 0,
    coolantTemp: live?.coolant_temperature_c ?? 0,
    healthScore: live?.overall_health_score ?? 0,

    ...behaviour,
    lastActive: live?.last_updated_at ?? null,

    totalDistanceKm: stats?.total_distance_km ?? 0,
    tripsCompleted: stats?.total_trips ?? 0,
    averageSpeedKmh:
      stats && stats.total_driving_time_seconds > 0
        ? Math.round(stats.total_distance_km / (stats.total_driving_time_seconds / 3600))
        : 0,
    fuelEfficiencyKmPerL: stats?.fuel_efficiency ?? 0,
    drivingHours: stats ? stats.total_driving_time_seconds / 3600 : 0,
    tripsToday: 0,
    performanceHistory: [],
    behaviourDistribution: buildBehaviourDistribution(stats),
  };
}

export function adaptDrivers(drivers, statistics, liveVehicles) {
  if (!Array.isArray(drivers)) return [];
  const statsById = new Map((statistics || []).map((s) => [s.driver_id, s]));
  const liveById = new Map((liveVehicles || []).map((v) => [v.driver_id, v]));
  return drivers.map((d) => adaptDriver(d, statsById.get(d.driver_id), liveById.get(d.driver_id)));
}

export function buildDriverRankings(drivers) {
  return [...drivers]
    .sort((a, b) => b.safetyScore - a.safetyScore)
    .map((d) => ({
      id: d.id,
      name: d.name,
      score: d.safetyScore,
      tripsCompleted: d.tripsCompleted,
      trend: d.trend,
      scoreDelta: d.scoreDelta ?? 0,
      scoreTrend: d.scoreTrend ?? null,
    }));
}
