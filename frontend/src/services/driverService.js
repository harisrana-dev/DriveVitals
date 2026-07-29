/**
 * Driver Service
 *
 * Future: replace mock imports with
 *   fetch('/api/drivers') or WebSocket subscription
 *
 * Expected backend:
 *   PostgreSQL → FastAPI → Analytics Engine → Driver Context → React
 */

import {
  driverProfiles,
  driverRankings,
} from '../mocks/drivers';

export function getDrivers() {
  return driverProfiles;
}

export function getDriverById(id) {
  return driverProfiles.find((d) => d.id === id) || null;
}

export function getDriverPerformance(driverId) {
  const driver = driverProfiles.find((d) => d.id === driverId);
  if (!driver) return null;
  return {
    history: driver.performanceHistory,
    breakdown: driver.scoreBreakdown,
    distribution: driver.behaviourDistribution,
  };
}

export function getDriverRanking() {
  return driverRankings;
}

export function getDriversOverview() {
  const total = driverProfiles.length;
  const active = driverProfiles.filter((d) => d.status === 'active').length;
  const highRisk = driverProfiles.filter((d) => d.riskLevel === 'high' || d.riskLevel === 'critical').length;
  const avgScore = Math.round(
    driverProfiles.reduce((s, d) => s + d.safetyScore, 0) / total
  );
  return { total, active, highRisk, avgScore };
}
