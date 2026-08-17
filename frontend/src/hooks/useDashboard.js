import { useMemo } from 'react';
import { useLiveData } from '../context/LiveDataContext';
import { useVehicles } from './useFleetData';
import { useAlerts, useLiveEvents } from './useAlerts';
import { useMaintenance } from './useMaintenance';
import { useNow } from './useNow';
import {
  computeFleetHealthAverage,
  computeActiveNowCount,
  deriveConnectionState,
  rankVehiclesForTriage,
  summarizeAttention,
  buildMaintenancePressureRows,
} from '../utils/dashboard';

/**
 * Single source of truth for the Dashboard page. Composes the canonical
 * data layer (vehicles, alerts, live events, maintenance) into dashboard
 * shape so every surface reconciles to the same numbers.
 *
 * `activeNow` is only a number while the connection is live; when the
 * socket is down or stale it is `null` — never a misleading zero.
 */
export function useDashboard() {
  const {
    connectionStatus,
    lastUpdate,
    fleetMeta,
    hydrated,
    syncing,
    sync,
  } = useLiveData();
  const now = useNow(5000);
  const vehicles = useVehicles();
  const alertsApi = useAlerts();
  const liveEvents = useLiveEvents();
  const maintenanceApi = useMaintenance();

  return useMemo(
    () => {
      const connState = deriveConnectionState(connectionStatus, lastUpdate, now);
      const triageRows = rankVehiclesForTriage(vehicles, {
        alerts: alertsApi.alerts,
        liveEvents,
        workItems: maintenanceApi.workItems,
      });
      return {
        vehicles,
        triageRows,
        attention: summarizeAttention(triageRows),
        alertsApi,
        maintenanceApi,
        liveEvents,
        fleetHealthScore: computeFleetHealthAverage(vehicles),
        activeNow: connState === 'live' ? computeActiveNowCount(vehicles) : null,
        totalFleet: vehicles.length,
        openAlerts: alertsApi.kpis,
        maintenancePressure: buildMaintenancePressureRows(
          maintenanceApi.workItems,
          fleetMeta
        ),
        connState,
        connectionStatus,
        lastUpdate,
        hydrated,
        syncing,
        sync,
      };
    },
    [
      vehicles,
      alertsApi,
      liveEvents,
      maintenanceApi,
      fleetMeta,
      connectionStatus,
      lastUpdate,
      now,
      hydrated,
      syncing,
      sync,
    ]
  );
}
