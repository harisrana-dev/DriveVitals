import { useMemo } from 'react';
import { useFleetContext } from '../context/FleetContext';
import {
  buildServiceQueue,
  buildDistribution,
  buildKpiStats,
  buildUpcomingSchedule,
  estimateFleetCost,
  buildServiceHistory,
  buildDrawerData,
} from '../utils/maintenance';

export function useMaintenance() {
  const { dashboard } = useFleetContext();
  return useMemo(() => {
    const vehicles = dashboard?.vehicles;
    if (!vehicles || !Array.isArray(vehicles) || vehicles.length === 0) {
      return {
        serviceQueue: [],
        distribution: [],
        kpiStats: { requiresService: 0, overdue: 0, upcoming: 0, compliancePct: 0, total: 0 },
        upcomingSchedule: [],
        fleetCost: { monthly: 0, upcoming: 0, critical: 0 },
        serviceHistory: [],
        vehicles: [],
      };
    }
    return {
      serviceQueue: buildServiceQueue(vehicles),
      distribution: buildDistribution(vehicles),
      kpiStats: buildKpiStats(vehicles),
      upcomingSchedule: buildUpcomingSchedule(vehicles),
      fleetCost: estimateFleetCost(vehicles),
      serviceHistory: buildServiceHistory(vehicles),
      vehicles,
    };
  }, [dashboard]);
}

export function useMaintenanceVehicle(vehicleId) {
  const { dashboard } = useFleetContext();
  return useMemo(() => {
    const vehicles = dashboard?.vehicles;
    if (!vehicles || !Array.isArray(vehicles)) return null;
    const vehicle = vehicles.find((v) => v.vehicle_id === vehicleId);
    if (!vehicle) return null;
    return { vehicle, drawerData: buildDrawerData(vehicle) };
  }, [dashboard, vehicleId]);
}
