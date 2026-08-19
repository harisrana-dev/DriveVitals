import { apiClient } from '../../api/apiClient';
import { endpoints } from '../../api/endpoints';

export async function getAnalyticsSummary(params = {}) {
  return apiClient.get(endpoints.analytics.summary, { params });
}

export async function getFleetTrend(params = {}) {
  return apiClient.get(endpoints.analytics.fleetTrend, { params });
}

export async function getDriverRanking(params = {}) {
  return apiClient.get(endpoints.analytics.drivers, { params });
}

export async function getDriverTrend(driverId, params = {}) {
  return apiClient.get(endpoints.analytics.driverTrend(driverId), { params });
}

export async function getSafetyDistribution() {
  return apiClient.get(endpoints.analytics.safetyDistribution);
}

export async function getVehicleAnalytics(params = {}) {
  return apiClient.get(endpoints.analytics.vehicles, { params });
}

export async function getTripAnalytics(params = {}) {
  return apiClient.get(endpoints.analytics.trips, { params });
}

export async function getEventBreakdown(params = {}) {
  return apiClient.get(endpoints.analytics.events, { params });
}

export async function getEventTrend(params = {}) {
  return apiClient.get(endpoints.analytics.eventsTrend, { params });
}

export async function getInsights(params = {}) {
  return apiClient.get(endpoints.analytics.insights, { params });
}
