import { apiClient } from './apiClient';
import { endpoints } from './endpoints';

const digitalTwinApi = {
  /** Simulation controller status. */
  async getStatus() {
    return apiClient.get(endpoints.digitalTwin.status);
  },

  /** Reset the simulation to the default fleet (admin-only). */
  async reset() {
    return apiClient.post(endpoints.digitalTwin.reset);
  },

  // -- Drivers --------------------------------------------------------------

  async listDrivers(params = {}) {
    return apiClient.get(endpoints.digitalTwin.drivers, { params });
  },

  async createDriver(payload) {
    return apiClient.post(endpoints.digitalTwin.drivers, payload);
  },

  async updateDriver(driverId, payload) {
    return apiClient.patch(endpoints.digitalTwin.driver(driverId), payload);
  },

  async deleteDriver(driverId) {
    return apiClient.delete(endpoints.digitalTwin.driver(driverId));
  },

  // -- Vehicles --------------------------------------------------------------

  async listVehicles(params = {}) {
    return apiClient.get(endpoints.digitalTwin.vehicles, { params });
  },

  async createVehicle(payload) {
    return apiClient.post(endpoints.digitalTwin.vehicles, payload);
  },

  async updateVehicle(vehicleId, payload) {
    return apiClient.patch(endpoints.digitalTwin.vehicle(vehicleId), payload);
  },

  async deleteVehicle(vehicleId) {
    return apiClient.delete(endpoints.digitalTwin.vehicle(vehicleId));
  },

  // -- Routes ----------------------------------------------------------------

  async listRoutes(params = {}) {
    return apiClient.get(endpoints.digitalTwin.routes, { params });
  },

  async createRoute(payload) {
    return apiClient.post(endpoints.digitalTwin.routes, payload);
  },

  async updateRoute(routeId, payload) {
    return apiClient.patch(endpoints.digitalTwin.route(routeId), payload);
  },

  async deleteRoute(routeId) {
    return apiClient.delete(endpoints.digitalTwin.route(routeId));
  },

  // -- Assignments -----------------------------------------------------------

  async listAssignments(isActive) {
    return apiClient.get(endpoints.digitalTwin.assignments, {
      params: isActive === undefined ? {} : { is_active: isActive },
    });
  },

  async createAssignment(payload) {
    return apiClient.post(endpoints.digitalTwin.assignments, payload);
  },

  async updateAssignment(assignmentId, payload) {
    return apiClient.patch(
      endpoints.digitalTwin.assignment(assignmentId),
      payload
    );
  },

  async deleteAssignment(assignmentId) {
    return apiClient.delete(endpoints.digitalTwin.assignment(assignmentId));
  },

  // -- Scenarios & runs -------------------------------------------------------

  async listScenarios(params = {}) {
    return apiClient.get(endpoints.digitalTwin.scenarios, { params });
  },

  async scenario(scenarioId) {
    return apiClient.get(endpoints.digitalTwin.scenario(scenarioId));
  },

  async createScenario(payload, assignmentIds = []) {
    return apiClient.post(endpoints.digitalTwin.scenarios, payload, {
      params: assignmentIds.length ? { assignment_ids: assignmentIds } : {},
    });
  },

  async updateScenario(scenarioId, payload) {
    return apiClient.patch(
      endpoints.digitalTwin.scenario(scenarioId),
      payload
    );
  },

  async deleteScenario(scenarioId) {
    return apiClient.delete(endpoints.digitalTwin.scenario(scenarioId));
  },

  async setScenarioAssignments(scenarioId, assignmentIds) {
    return apiClient.post(
      endpoints.digitalTwin.scenarioAssignments(scenarioId),
      assignmentIds
    );
  },

  async activateScenario(scenarioId) {
    return apiClient.post(endpoints.digitalTwin.scenarioActivate(scenarioId));
  },

  async launchScenario(scenarioId) {
    return apiClient.post(endpoints.digitalTwin.scenarioLaunch(scenarioId));
  },

  async stopScenario(scenarioId) {
    return apiClient.post(endpoints.digitalTwin.scenarioStop(scenarioId));
  },

  async listRuns(scenarioId, params = {}) {
    return apiClient.get(endpoints.digitalTwin.scenarioRuns(scenarioId), {
      params,
    });
  },
};

export { digitalTwinApi };
