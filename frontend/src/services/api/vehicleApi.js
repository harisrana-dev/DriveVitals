import { apiClient } from '../../api/apiClient';
import { endpoints } from '../../api/endpoints';

export async function listVehicles(params = {}) {
  return apiClient.get(endpoints.fleet.list, { params: { limit: 100, ...params } });
}

export async function getVehicle(vehicleId) {
  return apiClient.get(endpoints.fleet.vehicle(vehicleId));
}

export async function listVehicleHealth(params = {}) {
  return apiClient.get(endpoints.vehicleHealth.list, { params: { limit: 100, ...params } });
}

export async function getVehicleHealth(vehicleId) {
  return apiClient.get(endpoints.vehicleHealth.item(vehicleId));
}
