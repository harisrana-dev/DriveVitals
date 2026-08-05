import { apiClient } from '../../api/apiClient';
import { endpoints } from '../../api/endpoints';

export async function listDrivers(params = {}) {
  return apiClient.get(endpoints.drivers.list, { params: { limit: 100, ...params } });
}

export async function getDriver(driverId) {
  return apiClient.get(endpoints.drivers.driver(driverId));
}

export async function listDriverStatistics(params = {}) {
  return apiClient.get(endpoints.driverStatistics.list, { params: { limit: 100, ...params } });
}

export async function getDriverStatistics(driverId) {
  return apiClient.get(endpoints.driverStatistics.driver(driverId));
}
