import { apiClient } from '../../api/apiClient';
import { endpoints } from '../../api/endpoints';

export async function listAlerts(params = {}) {
  return apiClient.get(endpoints.alerts.list, { params: { limit: 100, ...params } });
}

export async function listVehicleAlerts(vehicleId, params = {}) {
  return apiClient.get(endpoints.alerts.vehicle(vehicleId), { params: { limit: 100, ...params } });
}

export async function acknowledgeAlert(alertId) {
  return apiClient.post(endpoints.alerts.acknowledge(alertId));
}

export async function resolveAlert(alertId) {
  return apiClient.post(endpoints.alerts.resolve(alertId));
}
