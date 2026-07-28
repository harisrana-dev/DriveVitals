import {
  vehicles as mockVehicles,
  drivers as mockDrivers,
  alerts as mockAlerts,
  maintenanceItems as mockMaintenance,
  dashboardSummary as mockSummary,
  telemetryData as mockTelemetry,
} from '../mocks/data';

export function getVehicles() {
  return mockVehicles;
}

export function getVehicleById(id) {
  return mockVehicles.find((v) => v.id === id);
}

export function getDrivers() {
  return mockDrivers;
}

export function getAlerts() {
  return mockAlerts;
}

export function getMaintenanceItems() {
  return mockMaintenance;
}

export function getDashboardSummary() {
  return mockSummary;
}

export function getTelemetryData() {
  return mockTelemetry;
}

export function getTopDrivers(count = 5) {
  return [...mockDrivers].sort((a, b) => b.safetyScore - a.safetyScore).slice(0, count);
}

export function getUnacknowledgedAlertCount() {
  return mockAlerts.filter((a) => !a.acknowledged).length;
}
