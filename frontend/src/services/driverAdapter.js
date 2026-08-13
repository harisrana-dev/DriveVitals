import { tripIsHistorical } from '../utils/trips';

/**
 * Driver adapter — maps raw REST + live WebSocket payloads into the
 * driver page's view model WITHOUT fabricating data.
 *
 * Every field traces to a real source, split into two NEVER-conflated
 * groups:
 *  - `live.*`      — current telemetry / operational state and the live
 *                    driver safety score broadcast in the dashboard
 *                    WebSocket snapshot.
 *  - `historical.*`— persisted driver statistics (GET /driver-statistics).
 *  - `behaviour`   — recorded behaviour event counts plus per-100 km
 *                    rates normalised by recorded distance.
 *
 * Unknown values are represented explicitly as `null` (rendered as "—")
 * and are never replaced with defaults like 100, 0 or fabricated counts.
 * A driver without a live snapshot has no live score (null), which is
 * NOT the same as a score of 100.
 */

function getInitials(name) {
  if (!name) return '--';
  return name.split(' ').map((n) => n[0]).join('').toUpperCase().slice(0, 2);
}

function mapStatus(opStatus) {
  if (opStatus === 'ACTIVE') return 'active';
  if (opStatus === 'IDLE') return 'off_duty';
  if (opStatus === 'TRIP COMPLETED') return 'off_duty';
  return 'offline';
}

function riskFor(score, aggression) {
  if (score == null) return 'unknown';
  if (score < 60 || (aggression != null && aggression < 60)) return 'critical';
  if (score < 75 || (aggression != null && aggression < 75)) return 'high';
  if (score < 85) return 'moderate';
  return 'low';
}

/**
 * Canonical safety letter grade, mirroring the backend's
 * `analytics.driver_statistics.safety.compute_grade`.
 */
export function computeGrade(score) {
  if (score == null) return null;
  if (score >= 90) return 'A';
  if (score >= 80) return 'B';
  if (score >= 70) return 'C';
  if (score >= 60) return 'D';
  return 'F';
}

function severityFor(count) {
  if (count >= 5) return 'severe';
  if (count > 0) return 'moderate';
  return 'none';
}

function ratePer100Km(count, distanceKm) {
  if (distanceKm == null || distanceKm <= 0) return null;
  return Math.round((count / distanceKm) * 1000) / 10;
}

function behaviourBlock(count, active, distanceKm) {
  const countValue = count ?? 0;
  return {
    count: countValue,
    active: !!active,
    severity: severityFor(countValue),
    ratePer100Km: ratePer100Km(countValue, distanceKm),
  };
}

function buildBehaviourEvents(stats, live, totalDistanceKm) {
  const blocks = {
    harshBraking: behaviourBlock(
      stats?.harsh_braking_events,
      live?.harsh_braking,
      totalDistanceKm
    ),
    aggressiveAcceleration: behaviourBlock(
      stats?.aggressive_throttle_events,
      live?.aggressive_throttle,
      totalDistanceKm
    ),
    overspeedEvents: behaviourBlock(
      stats?.speeding_events,
      live?.speeding,
      totalDistanceKm
    ),
    highRpmEvents: behaviourBlock(
      stats?.high_rpm_events,
      live?.high_rpm,
      totalDistanceKm
    ),
  };
  const totalEvents =
    blocks.harshBraking.count +
    blocks.aggressiveAcceleration.count +
    blocks.overspeedEvents.count +
    blocks.highRpmEvents.count;
  return {
    ...blocks,
    totalEvents,
    totalRatePer100Km: ratePer100Km(totalEvents, totalDistanceKm),
  };
}

function mapLiveRiskLevel(level) {
  if (
    level === 'low' ||
    level === 'moderate' ||
    level === 'high' ||
    level === 'critical'
  ) {
    return level;
  }
  return 'unknown';
}

function buildLive(driver, live) {
  return {
    score: live?.driver_safety_score == null ? null : Math.round(live.driver_safety_score),
    riskLevel: mapLiveRiskLevel(live?.driver_risk_level),
    status: mapStatus(live?.operational_status),
    vehicleId: live?.vehicle_id ?? null,
    vehicleName: live?.vehicle_name || null,
    telemetry: {
      speed: live?.speed_kmh ?? null,
      rpm: live?.rpm ?? null,
      throttle: live?.throttle_position_percent ?? null,
      brake: live?.brake_percent ?? null,
      fuelLevel: live?.fuel_level_percent ?? null,
      engineLoad: live?.engine_load_percent ?? null,
      coolantTemp: live?.coolant_temperature_c ?? null,
      healthScore: live?.overall_health_score ?? null,
    },
    activeEvents: live?.active_event_types || [],
    lastUpdated: live?.last_updated_at ?? null,
  };
}

function adaptDriver(driver, stats, live, driverTrips) {
  const name = `${driver.first_name || ''} ${driver.last_name || ''}`.trim() || driver.driver_id;
  const safetyScore = stats?.safety_score ?? null;
  const aggressionScore = stats?.aggression_score ?? null;
  const efficiencyScore = stats?.efficiency_score ?? null;

  const completedTrips = (driverTrips || []).filter(
    (t) => tripIsHistorical(t) && t.status === 'completed'
  );

  const scoredTrips = completedTrips.filter((t) => t.safetyScore != null);

  const todayKey = new Date().toDateString();
  const tripsToday = completedTrips.filter(
    (t) => t.completedAt && new Date(t.completedAt).toDateString() === todayKey
  ).length;

  const drivingTimeSeconds = stats?.total_driving_time_seconds ?? 0;
  const totalDistanceKm = stats?.total_distance_km ?? null;

  const liveBlock = buildLive(driver, live);

  const historical = {
    safetyScore: safetyScore == null ? null : Math.round(safetyScore),
    grade: computeGrade(safetyScore),
    riskLevel: riskFor(safetyScore, aggressionScore),
    scores: {
      safety: safetyScore == null ? null : Math.round(safetyScore),
      efficiency: efficiencyScore == null ? null : Math.round(efficiencyScore),
      aggression: aggressionScore == null ? null : Math.round(aggressionScore),
    },
    tripsCompleted: stats?.total_trips ?? null,
    totalDistanceKm,
    drivingHours: drivingTimeSeconds > 0 ? drivingTimeSeconds / 3600 : null,
    averageTripScore:
      stats?.average_trip_score == null ? null : Math.round(stats.average_trip_score),
    fuelEfficiency:
      stats?.fuel_efficiency != null && stats.fuel_efficiency > 0
        ? stats.fuel_efficiency
        : null,
    averageSpeedKmh:
      drivingTimeSeconds > 0
        ? Math.round(totalDistanceKm / (drivingTimeSeconds / 3600))
        : null,
    performanceHistory: [...scoredTrips].sort(
      (a, b) => new Date(a.completedAt || 0) - new Date(b.completedAt || 0)
    ),
    trend: null,
    scoreDelta: null,
    scoreTrend: null,
    percentile: null,
  };

  return {
    id: driver.driver_id,
    name,
    initials: getInitials(name),
    status: liveBlock.status,
    vehicleId: liveBlock.vehicleId,
    vehicleName: liveBlock.vehicleName,
    lastActive: live?.last_updated_at ?? null,
    tripsToday,
    live: liveBlock,
    historical,
    behaviour: buildBehaviourEvents(stats, live, totalDistanceKm),
  };
}

export function adaptDrivers(drivers, statistics, liveVehicles, trips) {
  if (!Array.isArray(drivers)) return [];
  const statsById = new Map((statistics || []).map((s) => [s.driver_id, s]));
  const liveById = new Map((liveVehicles || []).map((v) => [v.driver_id, v]));
  const tripsByDriver = new Map();
  for (const t of trips || []) {
    if (!t || !t.driverId) continue;
    if (!tripsByDriver.has(t.driverId)) tripsByDriver.set(t.driverId, []);
    tripsByDriver.get(t.driverId).push(t);
  }
  return drivers.map((d) =>
    adaptDriver(d, statsById.get(d.driver_id), liveById.get(d.driver_id), tripsByDriver.get(d.driver_id))
  );
}

/**
 * The operative risk level for a driver: the live risk while the driver
 * is actively driving (the urgent signal), otherwise the historical risk
 * from persisted statistics, otherwise 'unknown'. Never both at once.
 */
export function driverRiskLevel(d) {
  if (!d) return 'unknown';
  if (d.status === 'active' && d.live?.riskLevel && d.live.riskLevel !== 'unknown') {
    return d.live.riskLevel;
  }
  if (d.historical?.riskLevel) return d.historical.riskLevel;
  return 'unknown';
}

/**
 * The behaviour event type with the highest recorded count, used for the
 * leaderboard "Key Event" column. Returns null when nothing is recorded.
 */
export function leadingBehaviour(d) {
  const b = d?.behaviour;
  if (!b || b.totalEvents === 0) return null;
  const order = [
    ['harshBraking', 'Harsh Braking'],
    ['aggressiveAcceleration', 'Aggressive Acceleration'],
    ['overspeedEvents', 'Speeding'],
    ['highRpmEvents', 'High RPM'],
  ];
  let best = null;
  let bestCount = -1;
  for (const [key, label] of order) {
    const count = b[key]?.count ?? 0;
    if (count > bestCount) {
      bestCount = count;
      best = label;
    }
  }
  return bestCount > 0 ? best : null;
}

export function buildDriverRankings(drivers) {
  return [...drivers]
    .filter((d) => d.historical?.safetyScore != null)
    .sort((a, b) => b.historical.safetyScore - a.historical.safetyScore)
    .map((d) => ({
      id: d.id,
      name: d.name,
      score: d.historical.safetyScore,
      tripsCompleted: d.historical.tripsCompleted,
      trend: d.historical.trend || null,
      scoreDelta: d.historical.scoreDelta ?? null,
      scoreTrend: d.historical.scoreTrend ?? null,
    }));
}
