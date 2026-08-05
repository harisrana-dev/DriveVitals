import { apiClient } from '../../api/apiClient';
import { endpoints } from '../../api/endpoints';

export async function getSystemHealth() {
  return apiClient.get(endpoints.health.check);
}

export async function getSystemStatus() {
  return apiClient.get(endpoints.health.status);
}

export async function getSystemVersion() {
  return apiClient.get(endpoints.health.version);
}
