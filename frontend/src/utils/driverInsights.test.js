import { describe, expect, it } from 'vitest';
import { generateDriverInsights } from './driverInsights';

function behaviour(overrides = {}) {
  return {
    overspeedEvents: { count: 2 },
    harshBraking: { count: 1 },
    aggressiveAcceleration: { count: 1 },
    highRpmEvents: { count: 0 },
    totalEvents: 4,
    ...overrides,
  };
}

function driver(name, overrides = {}) {
  return {
    id: name,
    name,
    status: 'off_duty',
    live: { riskLevel: 'unknown' },
    historical: {
      tripsCompleted: 8,
      safetyScore: 84,
      riskLevel: 'low',
      scores: { safety: 84, efficiency: 78, aggression: 90 },
      performanceHistory: [],
      ...(overrides.historical || {}),
    },
    behaviour: behaviour(overrides.behaviour),
    ...overrides,
  };
}

const fleet = [
  driver('B', { historical: { safetyScore: 90 } }),
  driver('C', { historical: { safetyScore: 86 } }),
  driver('D', { historical: { safetyScore: 95 } }),
];

function scores(...values) {
  return values.map((score, i) => ({
    score,
    completedAt: `2026-0${(i % 9) + 1}-01T00:00:00Z`,
  }));
}

describe('generateDriverInsights', () => {
  it('emits a single no-trips insight and stops early', () => {
    const d = driver('A', { historical: { tripsCompleted: 0 } });
    const insights = generateDriverInsights({ driver: d, allDrivers: fleet });
    expect(insights).toHaveLength(1);
    expect(insights[0]).toMatchObject({
      id: 'no-trips',
      severity: 'info',
      title: 'No completed trips recorded',
    });
  });

  it('flags a driver below the fleet-average safety', () => {
    const d = driver('A', { historical: { safetyScore: 70, scores: { safety: 70 } } });
    const insights = generateDriverInsights({ driver: d, allDrivers: fleet });
    const bench = insights.find((i) => i.id === 'fleet-benchmark');
    expect(bench).toMatchObject({
      severity: 'critical',
      title: 'Below fleet-average safety',
    });
    expect(bench.observation).toContain('20 points below');
  });

  it('credits a driver above the fleet-average safety', () => {
    const insights = generateDriverInsights({
      driver: driver('A', { historical: { safetyScore: 96, scores: { safety: 96 } } }),
      allDrivers: fleet,
    });
    const bench = insights.find((i) => i.id === 'fleet-benchmark');
    expect(bench).toMatchObject({
      severity: 'info',
      title: 'Above fleet-average safety',
    });
  });

  it('identifies the leading behaviour event from real counts', () => {
    const d = driver('A', {
      behaviour: behaviour({
        overspeedEvents: { count: 9 },
        harshBraking: { count: 1 },
        totalEvents: 10,
      }),
    });
    const insights = generateDriverInsights({ driver: d, allDrivers: fleet });
    const leading = insights.find((i) => i.id === 'leading-behaviour');
    expect(leading).toMatchObject({
      title: 'Overspeed is the leading behaviour event',
      severity: 'high',
    });
  });

  it('emits an overspeed-share insight when most events are speeding', () => {
    const d = driver('A', {
      behaviour: behaviour({
        overspeedEvents: { count: 6 },
        harshBraking: { count: 2 },
        aggressiveAcceleration: { count: 2 },
        totalEvents: 10,
      }),
    });
    const insights = generateDriverInsights({ driver: d, allDrivers: fleet });
    expect(insights.find((i) => i.id === 'overspeed-share')).toBeTruthy();
  });

  it('does not emit an overspeed-share insight without enough share', () => {
    const d = driver('A', {
      behaviour: behaviour({
        overspeedEvents: { count: 1 },
        harshBraking: { count: 3 },
        aggressiveAcceleration: { count: 3 },
        totalEvents: 7,
      }),
    });
    const insights = generateDriverInsights({ driver: d, allDrivers: fleet });
    expect(insights.find((i) => i.id === 'overspeed-share')).toBeUndefined();
  });

  it('emits a declining trend insight from recorded scores only', () => {
    const d = driver('A', {
      historical: {
        tripsCompleted: 6,
        safetyScore: 70,
        scores: { safety: 70, efficiency: 70, aggression: 70 },
        riskLevel: 'high',
        performanceHistory: scores(95, 90, 88, 80, 75, 70),
      },
    });
    const insights = generateDriverInsights({ driver: d, allDrivers: fleet });
    expect(insights.find((i) => i.id === 'safety-trend')).toMatchObject({
      severity: 'high',
      title: 'Safety score is declining',
    });
  });

  it('emits an improving trend insight from recorded scores only', () => {
    const d = driver('A', {
      historical: {
        tripsCompleted: 6,
        safetyScore: 90,
        scores: { safety: 90, efficiency: 80, aggression: 80 },
        riskLevel: 'low',
        performanceHistory: scores(70, 75, 78, 90, 92, 95),
      },
    });
    const insights = generateDriverInsights({ driver: d, allDrivers: fleet });
    expect(insights.find((i) => i.id === 'safety-trend-up')).toMatchObject({
      severity: 'info',
      title: 'Safety score is improving',
    });
  });

  it('does not emit a trend insight from a single scored trip', () => {
    const d = driver('A', {
      historical: {
        tripsCompleted: 1,
        safetyScore: 40,
        scores: { safety: 40 },
        riskLevel: 'critical',
        performanceHistory: scores(40),
      },
    });
    const insights = generateDriverInsights({ driver: d, allDrivers: fleet });
    expect(insights.find((i) => i.id === 'safety-trend')).toBeUndefined();
    expect(insights.find((i) => i.id === 'safety-trend-up')).toBeUndefined();
  });

  it('flags partial score data without inventing values', () => {
    const d = driver('A', {
      historical: {
        tripsCompleted: 3,
        safetyScore: 82,
        scores: { safety: 82, efficiency: null, aggression: null },
        riskLevel: 'low',
      },
    });
    const insights = generateDriverInsights({ driver: d, allDrivers: fleet });
    const partial = insights.find((i) => i.id === 'partial-scores');
    expect(partial).toMatchObject({
      severity: 'info',
      title: 'Partial score data',
    });
    expect(partial.observation).toContain('Efficiency and Aggression scores are');
  });
});
