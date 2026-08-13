/**
 * Fleet benchmark for a single driver.
 *
 * Percentiles and fleet averages are computed from real historical
 * driver safety scores only. The benchmark is intentionally null until
 * the fleet has enough scored drivers to be meaningful — never a
 * fabricated "top of fleet" badge.
 */

export const BENCHMARK_MIN_SCORED_DRIVERS = 3;

function fleetScored(allDrivers) {
  return (allDrivers || []).filter(
    (d) => d && d.historical?.safetyScore != null
  );
}

export function computeDriverBenchmark(driver, allDrivers) {
  if (!driver || driver.historical?.safetyScore == null) return null;

  const scored = fleetScored(allDrivers);
  if (scored.length < BENCHMARK_MIN_SCORED_DRIVERS) return null;

  const fleetAvg =
    scored.reduce((sum, d) => sum + d.historical.safetyScore, 0) / scored.length;
  const percentile =
    driver.historical.percentile != null
      ? driver.historical.percentile
      : Math.round(
          (scored.filter((d) => d.historical.safetyScore <= driver.historical.safetyScore).length /
            scored.length) *
            100
        );

  const fleetDistance = scored.reduce(
    (sum, d) => sum + (d.historical.totalDistanceKm || 0),
    0
  );
  const driverDistance = driver.historical.totalDistanceKm || 0;
  const fleetEventRate =
    fleetDistance > 0
      ? (scored.reduce((sum, d) => sum + d.behaviour.totalEvents, 0) / fleetDistance) *
        100
      : null;
  const driverEventRate =
    driverDistance > 0
      ? (driver.behaviour.totalEvents / driverDistance) * 100
      : null;

  const withFuel = scored.filter(
    (d) => d.historical?.fuelEfficiency != null
  );
  const fleetFuelEfficiency =
    withFuel.length >= BENCHMARK_MIN_SCORED_DRIVERS
      ? withFuel.reduce((sum, d) => sum + d.historical.fuelEfficiency, 0) /
        withFuel.length
      : null;

  return {
    fleetSize: scored.length,
    fleetAvg: Math.round(fleetAvg),
    percentile,
    diff: Math.round(driver.historical.safetyScore - fleetAvg),
    driverEventRate,
    fleetEventRate,
    fleetFuelEfficiency:
      fleetFuelEfficiency == null ? null : Math.round(fleetFuelEfficiency * 100) / 100,
  };
}
