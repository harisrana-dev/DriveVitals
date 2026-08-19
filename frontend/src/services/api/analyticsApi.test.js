import { describe, it, expect } from 'vitest';
import { endpoints } from '../../api/endpoints';

describe('Analytics API endpoints', () => {
  it('has all required analytics endpoint paths', () => {
    expect(endpoints.analytics.summary).toBe('/analytics/summary');
    expect(endpoints.analytics.fleetTrend).toBe('/analytics/fleet-trend');
    expect(endpoints.analytics.drivers).toBe('/analytics/drivers');
    expect(endpoints.analytics.driverTrend('D-01')).toBe('/analytics/drivers/D-01/trend');
    expect(endpoints.analytics.safetyDistribution).toBe('/analytics/safety-distribution');
    expect(endpoints.analytics.vehicles).toBe('/analytics/vehicles');
    expect(endpoints.analytics.trips).toBe('/analytics/trips');
    expect(endpoints.analytics.events).toBe('/analytics/events');
    expect(endpoints.analytics.eventsTrend).toBe('/analytics/events/trend');
    expect(endpoints.analytics.insights).toBe('/analytics/insights');
  });
});
