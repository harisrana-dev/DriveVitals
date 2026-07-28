import { useMemo } from 'react';
import * as fleetService from '../services/fleetService';

export function useVehicles() {
  return useMemo(() => fleetService.getVehicles(), []);
}

export function useVehicle(id) {
  return useMemo(() => fleetService.getVehicleById(id), [id]);
}

export function useDrivers() {
  return useMemo(() => fleetService.getDrivers(), []);
}

export function useTopDrivers(count) {
  return useMemo(() => fleetService.getTopDrivers(count), [count]);
}

export function useAlerts() {
  return useMemo(() => fleetService.getAlerts(), []);
}

export function useMaintenanceItems() {
  return useMemo(() => fleetService.getMaintenanceItems(), []);
}

export function useDashboardSummary() {
  return useMemo(() => fleetService.getDashboardSummary(), []);
}

export function useTelemetryData() {
  return useMemo(() => fleetService.getTelemetryData(), []);
}

export function useUnacknowledgedAlertCount() {
  return useMemo(() => fleetService.getUnacknowledgedAlertCount(), []);
}
