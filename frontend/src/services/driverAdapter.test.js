import { describe, expect, it } from 'vitest';
import {
  adaptDrivers,
  computeGrade,
  driverRiskLevel,
  leadingBehaviour,
  buildDriverRankings,
} from './driverAdapter';

describe('computeGrade', () => {
  it('mirrors the backend grade bands', () => {
    expect(computeGrade(95)).toBe('A');
    expect(computeGrade(90)).toBe('A');
    expect(computeGrade(89)).toBe('B');
    expect(computeGrade(80)).toBe('B');
    expect(computeGrade(79)).toBe('C');
    expect(computeGrade(70)).toBe('C');
    expect(computeGrade(69)).toBe('D');
    expect(computeGrade(60)).toBe('D');
    expect(computeGrade(59)).toBe('F');
    expect(computeGrade(0)).toBe('F');
  });

  it('returns null for missing scores', () => {
    expect(computeGrade(null)).toBeNull();
    expect(computeGrade(undefined)).toBeNull();
  });
});

describe('driverRiskLevel', () => {
  it('prefers live risk while the driver is active', () => {
    const d = {
      status: 'active',
      live: { riskLevel: 'critical' },
      historical: { riskLevel: 'low' },
    };
    expect(driverRiskLevel(d)).toBe('critical');
  });

  it('falls back to historical risk when not active', () => {
    const d = {
      status: 'off_duty',
      live: { riskLevel: 'critical' },
      historical: { riskLevel: 'moderate' },
    };
    expect(driverRiskLevel(d)).toBe('moderate');
  });

  it('never conflates live and historical: active driver ignores historical', () => {
    const d = {
      status: 'active',
      live: { riskLevel: 'unknown' },
      historical: { riskLevel: 'high' },
    };
    expect(driverRiskLevel(d)).toBe('high');
  });

  it('returns unknown for drivers with no score data', () => {
    expect(driverRiskLevel({})).toBe('unknown');
    expect(driverRiskLevel(null)).toBe('unknown');
  });
});

describe('leadingBehaviour', () => {
  it('returns the label of the highest-count event', () => {
    const d = {
      behaviour: {
        totalEvents: 7,
        harshBraking: { count: 1 },
        aggressiveAcceleration: { count: 2 },
        overspeedEvents: { count: 4 },
        highRpmEvents: { count: 0 },
      },
    };
    expect(leadingBehaviour(d)).toBe('Speeding');
  });

  it('returns null when nothing is recorded', () => {
    expect(leadingBehaviour({ behaviour: { totalEvents: 0 } })).toBeNull();
  });
});

describe('adaptDrivers', () => {
  const rawDrivers = [{ driver_id: 'D1', first_name: 'Ada', last_name: 'Lovelace' }];
  const stats = [
    {
      driver_id: 'D1',
      safety_score: 92,
      aggression_score: 88,
      efficiency_score: 70,
      total_trips: 6,
      total_distance_km: 420,
      total_driving_time_seconds: 14400,
      average_trip_score: 85,
      fuel_efficiency: 14.2,
      speeding_events: 3,
      harsh_braking_events: 1,
      aggressive_throttle_events: 0,
      high_rpm_events: 2,
    },
  ];
  const live = [
    {
      driver_id: 'D1',
      operational_status: 'ACTIVE',
      driver_safety_score: 74.4,
      driver_risk_level: 'high',
      vehicle_id: 'V9',
      vehicle_name: 'Unit 9',
      speed_kmh: 63,
      rpm: 2400,
      throttle_position_percent: 42,
      brake_percent: 0,
      fuel_level_percent: 51,
      engine_load_percent: 60,
      coolant_temperature_c: 88,
      overall_health_score: 97,
      speeding: true,
      aggressive_throttle: false,
      harsh_braking: false,
      high_rpm: false,
      active_event_types: ['speeding'],
      last_updated_at: '2026-08-13T10:00:00Z',
    },
  ];
  const trips = [
    {
      driverId: 'D1',
      status: 'completed',
      safetyScore: 90,
      completedAt: '2026-08-01T09:00:00Z',
      distanceFormatted: '120 km',
      routeId: 'R1',
    },
    {
      driverId: 'D1',
      status: 'completed',
      safetyScore: 82,
      completedAt: '2026-08-05T09:00:00Z',
      distanceFormatted: '80 km',
      routeId: 'R2',
    },
    {
      driverId: 'D1',
      status: 'in_progress',
      safetyScore: null,
      completedAt: null,
    },
  ];

  const [d] = adaptDrivers(rawDrivers, stats, live, trips);

  it('separates live and historical score groups without fabrication', () => {
    expect(d.live.score).toBe(74);
    expect(d.live.riskLevel).toBe('high');
    expect(d.live.status).toBe('active');
    expect(d.live.vehicleId).toBe('V9');
    expect(d.historical.safetyScore).toBe(92);
    expect(d.historical.grade).toBe('A');
    expect(d.historical.riskLevel).toBe('low');
    expect(d.historical.tripsCompleted).toBe(6);
    expect(d.historical.scores).toEqual({ safety: 92, efficiency: 70, aggression: 88 });
    expect(d.historical.trend).toBeNull();
    expect(d.historical.scoreDelta).toBeNull();
    expect(d.historical.percentile).toBeNull();
  });

  it('keeps live telemetry and active events under live.*', () => {
    expect(d.live.telemetry.speed).toBe(63);
    expect(d.live.telemetry.rpm).toBe(2400);
    expect(d.live.telemetry.fuelLevel).toBe(51);
    expect(d.live.activeEvents).toEqual(['speeding']);
    expect(d.live.lastUpdated).toBe('2026-08-13T10:00:00Z');
  });

  it('builds behaviour blocks with counts, severity and per-100 km rates', () => {
    expect(d.behaviour.totalEvents).toBe(6);
    expect(d.behaviour.overspeedEvents.count).toBe(3);
    expect(d.behaviour.overspeedEvents.active).toBe(true);
    expect(d.behaviour.overspeedEvents.severity).toBe('moderate');
    expect(d.behaviour.harshBraking.count).toBe(1);
    expect(d.behaviour.highRpmEvents.count).toBe(2);
    expect(d.behaviour.totalRatePer100Km).toBe(1.4);
  });

  it('only keeps completed trips in the performance history', () => {
    expect(d.historical.performanceHistory).toHaveLength(2);
    expect(d.historical.performanceHistory.map((t) => t.safetyScore)).toEqual([90, 82]);
  });

  it('drives derived metrics from recorded distance and time', () => {
    expect(d.historical.drivingHours).toBe(4);
    expect(d.historical.averageSpeedKmh).toBe(105);
    expect(d.historical.averageTripScore).toBe(85);
    expect(d.historical.fuelEfficiency).toBe(14.2);
  });
});

describe('adaptDrivers with no live snapshot', () => {
  it('emits a null live score — never a fabricated 100', () => {
    const [d] = adaptDrivers(
      [{ driver_id: 'D2', first_name: 'Bob', last_name: 'Oden' }],
      [{ driver_id: 'D2', safety_score: 55, total_trips: 1 }],
      [],
      []
    );
    expect(d.live.score).toBeNull();
    expect(d.historical.safetyScore).toBe(55);
    expect(d.historical.grade).toBe('F');
    expect(d.historical.riskLevel).toBe('critical');
    expect(d.historical.performanceHistory).toEqual([]);
    expect(d.behaviour.totalEvents).toBe(0);
  });
});

describe('buildDriverRankings', () => {
  it('ranks only scored drivers by historical safety, descending', () => {
    const drivers = [
      { id: 'A', historical: { safetyScore: 70 } },
      { id: 'B', historical: { safetyScore: 95 } },
      { id: 'C', historical: { safetyScore: null } },
    ];
    const ranked = buildDriverRankings(drivers);
    expect(ranked.map((r) => r.id)).toEqual(['B', 'A']);
  });
});
