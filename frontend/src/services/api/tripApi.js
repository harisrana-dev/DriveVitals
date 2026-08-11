import { apiClient } from '../../api/apiClient';
import { endpoints } from '../../api/endpoints';

export async function listTrips(params = {}) {
  return apiClient.get(endpoints.trips.list, { params: { limit: 100, ...params } });
}

export async function getTrip(tripId) {
  return apiClient.get(endpoints.trips.item(tripId));
}

export async function deleteTrip(tripId) {
  return apiClient.delete(endpoints.trips.item(tripId));
}

export async function deleteAbortedTrips() {
  return apiClient.delete(endpoints.trips.aborted);
}
