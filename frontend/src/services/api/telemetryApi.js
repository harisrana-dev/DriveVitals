import { apiClient } from '../../api/apiClient';
import { endpoints } from '../../api/endpoints';

export async function listTelemetry(params = {}) {
  return apiClient.get(endpoints.telemetry.list, { params: { limit: 100, ...params } });
}

export async function listLatestTelemetry(params = {}) {
  return apiClient.get(endpoints.telemetry.list, { params: { latest: true, limit: 100, ...params } });
}

export async function listVehicleTelemetry(vehicleId, params = {}) {
  return apiClient.get(endpoints.telemetry.vehicle(vehicleId), { params: { limit: 100, ...params } });
}
