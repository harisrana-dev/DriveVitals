import { apiClient } from '../../api/apiClient';
import { endpoints } from '../../api/endpoints';

export async function listMaintenance(params = {}) {
  return apiClient.get(endpoints.maintenance.list, { params: { limit: 100, ...params } });
}

export async function listVehicleMaintenance(vehicleId, params = {}) {
  return apiClient.get(endpoints.maintenance.item(vehicleId), { params: { limit: 100, ...params } });
}
