import { describe, expect, it } from 'vitest';
import { computeDriverBenchmark, BENCHMARK_MIN_SCORED_DRIVERS } from './driverBenchmark';

function driver(id, safetyScore, overrides = {}) {
  return {
    id,
    name: `Driver ${id}`,
    historical: {
      safetyScore,
      scoreQuality: 'valid',
      totalDistanceKm: 300,
      fuelEfficiency: 14,
      percentile: null,
      ...(overrides.historical || {}),
    },
    behaviour: {
      totalEvents: 3,
      ...(overrides.behaviour || {}),
    },
  };
}

describe('computeDriverBenchmark', () => {
  it('returns null for an unscored driver — never a fabricated rank', () => {
    const d = driver('A', null);
    expect(computeDriverBenchmark(d, [driver('B', 90), driver('C', 80)])).toBeNull();
  });

  it('returns null until the fleet has enough scored drivers', () => {
    const d = driver('A', 85);
    const fleet = [driver('B', 90), driver('C', 80)];
    expect(fleet.length).toBeLessThan(BENCHMARK_MIN_SCORED_DRIVERS);
    expect(computeDriverBenchmark(d, fleet)).toBeNull();
  });

  it('computes percentile among scored drivers only', () => {
    const d = driver('A', 85);
    const fleet = [
      driver('B', 70),
      driver('C', 80),
      driver('D', 85),
      driver('E', 95),
      driver('F', 100, { historical: { safetyScore: null } }),
    ];
    const benchmark = computeDriverBenchmark(d, fleet);
    expect(benchmark.fleetSize).toBe(4);
    expect(benchmark.percentile).toBe(75);
  });

  it('reuses the recorded percentile when present', () => {
    const d = driver('A', 85, { historical: { percentile: 92 } });
    const fleet = [driver('B', 90), driver('C', 80), driver('D', 95)];
    const benchmark = computeDriverBenchmark(d, fleet);
    expect(benchmark.percentile).toBe(92);
  });

  it('computes fleet average and the driver diff', () => {
    const d = driver('A', 70);
    const fleet = [driver('B', 90), driver('C', 80), driver('D', 100)];
    const benchmark = computeDriverBenchmark(d, fleet);
    expect(benchmark.fleetAvg).toBe(90);
    expect(benchmark.diff).toBe(-20);
  });

  it('normalises event rates per 100 km', () => {
    const d = driver('A', 85, {
      historical: { totalDistanceKm: 200 },
      behaviour: { totalEvents: 4 },
    });
    const fleet = [
      driver('B', 90, { historical: { totalDistanceKm: 300 }, behaviour: { totalEvents: 3 } }),
      driver('C', 80, { historical: { totalDistanceKm: 100 }, behaviour: { totalEvents: 1 } }),
      driver('D', 95, { historical: { totalDistanceKm: 500 }, behaviour: { totalEvents: 5 } }),
    ];
    const benchmark = computeDriverBenchmark(d, fleet);
    expect(benchmark.driverEventRate).toBe(2);
    expect(benchmark.fleetEventRate).toBe(1);
  });

  it('omits fuel-efficiency average when fewer than three drivers report it', () => {
    const d = driver('A', 85, { historical: { fuelEfficiency: 14 } });
    const fleet = [
      driver('B', 90, { historical: { fuelEfficiency: 12 } }),
      driver('C', 80, { historical: { fuelEfficiency: null } }),
      driver('D', 95, { historical: { fuelEfficiency: null } }),
    ];
    const benchmark = computeDriverBenchmark(d, fleet);
    expect(benchmark.fleetFuelEfficiency).toBeNull();
  });
});
