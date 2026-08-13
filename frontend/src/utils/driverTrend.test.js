import { describe, expect, it } from 'vitest';
import {
  classifyTrend,
  computeDriverTrend,
  TREND_DELTA_THRESHOLD,
} from './driverTrend';

describe('classifyTrend', () => {
  it('uses the strict delta threshold so small changes are stable', () => {
    expect(classifyTrend(TREND_DELTA_THRESHOLD + 0.1)).toBe('improving');
    expect(classifyTrend(TREND_DELTA_THRESHOLD)).toBe('stable');
    expect(classifyTrend(-(TREND_DELTA_THRESHOLD + 0.1))).toBe('declining');
    expect(classifyTrend(-TREND_DELTA_THRESHOLD)).toBe('stable');
    expect(classifyTrend(0)).toBe('stable');
  });
});

describe('computeDriverTrend', () => {
  it('returns null until enough scored trips exist', () => {
    const scores = [
      { score: 80, completedAt: '2026-01-01' },
      { score: 82, completedAt: '2026-01-02' },
      { score: 84, completedAt: '2026-01-03' },
    ];
    expect(computeDriverTrend(scores)).toBeNull();
  });

  it('never reports a trend from a single good trip', () => {
    const scores = [
      { score: 100, completedAt: '2026-01-01' },
      { score: 50, completedAt: '2026-01-02' },
      { score: 51, completedAt: '2026-01-03' },
      { score: 52, completedAt: '2026-01-04' },
    ];
    const trend = computeDriverTrend(scores);
    expect(trend).not.toBeNull();
    expect(trend.direction).toBe('declining');
  });

  it('sorts unordered observations chronologically before comparison', () => {
    const scores = [
      { score: 84, completedAt: '2026-01-03' },
      { score: 80, completedAt: '2026-01-01' },
      { score: 95, completedAt: '2026-01-04' },
      { score: 82, completedAt: '2026-01-02' },
    ];
    const trend = computeDriverTrend(scores);
    expect(trend.observations).toBe(4);
    expect(trend.direction).toBe('improving');
  });

  it('computes delta between recent and previous windows', () => {
    const scores = [
      { score: 70, completedAt: '2026-01-01' },
      { score: 70, completedAt: '2026-01-02' },
      { score: 70, completedAt: '2026-01-03' },
      { score: 90, completedAt: '2026-01-04' },
      { score: 90, completedAt: '2026-01-05' },
      { score: 90, completedAt: '2026-01-06' },
    ];
    const trend = computeDriverTrend(scores);
    expect(trend.recentAvg).toBe(90);
    expect(trend.previousAvg).toBe(70);
    expect(trend.delta).toBe(20);
    expect(trend.direction).toBe('improving');
  });

  it('ignores trips without a score and applies the minObservations override', () => {
    const scores = [
      { score: null, completedAt: '2026-01-01' },
      { score: 80, completedAt: '2026-01-02' },
      { score: 82, completedAt: '2026-01-03' },
      { score: 84, completedAt: '2026-01-04' },
    ];
    expect(computeDriverTrend(scores)).toBeNull();
    const fourValid = [
      { score: 70, completedAt: '2026-01-01' },
      { score: 80, completedAt: '2026-01-02' },
      { score: 90, completedAt: '2026-01-03' },
      { score: 95, completedAt: '2026-01-04' },
    ];
    expect(computeDriverTrend(fourValid, { minObservations: 3 })).not.toBeNull();
    expect(computeDriverTrend(fourValid, { minObservations: 5 })).toBeNull();
  });

  it('uses the options override for the recent window', () => {
    const scores = [
      { score: 50, completedAt: '2026-01-01' },
      { score: 50, completedAt: '2026-01-02' },
      { score: 90, completedAt: '2026-01-03' },
      { score: 90, completedAt: '2026-01-04' },
    ];
    const trend = computeDriverTrend(scores, {
      minObservations: 4,
      recentCount: 2,
    });
    expect(trend.direction).toBe('improving');
    expect(trend.recentAvg).toBe(90);
    expect(trend.previousAvg).toBe(50);
  });
});
