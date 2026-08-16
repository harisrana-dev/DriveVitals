import { useMemo, useState, useCallback } from 'react';
import { useLiveData } from '../context/LiveDataContext';
import {
  normalizeMaintenanceRecords,
  groupMaintenanceWorkItems,
  computeMaintenanceKpis,
  computeVehicleMaintenanceRisk,
  computeServiceWorkload,
  computeMaintenanceHorizon,
  computeMaintenanceInsights,
  sortMaintenanceHistory,
  filterMaintenanceWorkItems,
  sortMaintenanceWorkItems,
} from '../utils/maintenance';

const DEFAULT_FILTERS = {
  statusTab: 'all',
  dueWithin2000: false,
  priority: 'all',
  type: 'all',
  vehicleSearch: '',
  driverSearch: '',
};

/**
 * Canonical Maintenance hook. Every consumer on the Maintenance page
 * derives from the same normalized records and grouped work items, so the
 * KPI strip, attention queue, intelligence panels, work queue and drawer
 * all reconcile to the same numbers.
 */
export function useMaintenance() {
  const { maintenance, fleetMeta } = useLiveData();

  return useMemo(() => {
    const pending = (Array.isArray(maintenance) ? maintenance : []).filter(
      (r) => r && r.status === 'pending'
    );
    const records = normalizeMaintenanceRecords(pending, fleetMeta);
    const workItems = groupMaintenanceWorkItems(records);
    const vehicleRisk = computeVehicleMaintenanceRisk(workItems, fleetMeta);
    return {
      records,
      workItems,
      kpis: computeMaintenanceKpis(workItems),
      vehicleRisk,
      workload: computeServiceWorkload(workItems),
      horizon: computeMaintenanceHorizon(workItems),
      insights: computeMaintenanceInsights(workItems, vehicleRisk),
      history: sortMaintenanceHistory(maintenance, fleetMeta),
    };
  }, [maintenance, fleetMeta]);
}

/**
 * Vehicle-scoped maintenance data for the drawer: pending work items,
 * real completed history and maintenance-related alerts for the vehicle.
 */
export function useMaintenanceVehicle(vehicleId) {
  const { maintenance, fleetMeta, mergedFleet, alerts } = useLiveData();

  return useMemo(() => {
    const vehicle = (Array.isArray(mergedFleet) ? mergedFleet : null)?.find(
      (v) => v.vehicle_id === vehicleId
    ) || null;

    const vehicleRecords = (Array.isArray(maintenance) ? maintenance : []).filter(
      (r) => r && r.vehicle_id === vehicleId
    );

    const workItems = groupMaintenanceWorkItems(
      normalizeMaintenanceRecords(
        vehicleRecords.filter((r) => r.status === 'pending'),
        fleetMeta
      )
    );

    const completed = sortMaintenanceHistory(vehicleRecords, fleetMeta);

    const relatedAlerts = (Array.isArray(alerts) ? alerts : []).filter(
      (a) =>
        a &&
        a.vehicle_id === vehicleId &&
        (a.alert_type === 'maintenance' ||
          a.category === 'maintenance' ||
          a.alert_type === 'health')
    );

    return {
      vehicle,
      workItems,
      completed,
      relatedAlerts,
      kpis: computeMaintenanceKpis(workItems),
    };
  }, [vehicleId, maintenance, fleetMeta, mergedFleet, alerts]);
}

/**
 * Full filter API for the Maintenance page. State lives here and is lifted
 * to the page so the KPI strip, tabs, filters bar and work queue share one
 * source of truth.
 */
export function useMaintenanceFilters() {
  const [filters, setFilters] = useState(DEFAULT_FILTERS);

  const setStatusTab = useCallback(
    (v) => setFilters((f) => ({ ...f, statusTab: v, dueWithin2000: false })),
    []
  );
  const setPriority = useCallback(
    (v) => setFilters((f) => ({ ...f, priority: v })),
    []
  );
  const setType = useCallback(
    (v) => setFilters((f) => ({ ...f, type: v })),
    []
  );
  const setVehicleSearch = useCallback(
    (v) => setFilters((f) => ({ ...f, vehicleSearch: v })),
    []
  );
  const setDriverSearch = useCallback(
    (v) => setFilters((f) => ({ ...f, driverSearch: v })),
    []
  );
  const resetFilters = useCallback(() => setFilters(DEFAULT_FILTERS), []);

  const { workItems } = useMaintenance();

  /**
   * Clicking a KPI lifts the matching population to the work queue.
   */
  const applyKpiPreset = useCallback((key) => {
    setFilters((f) => {
      const base = {
        ...f,
        priority: 'all',
        type: 'all',
        vehicleSearch: '',
        driverSearch: '',
      };
      switch (key) {
        case 'overdue':
          return { ...base, statusTab: 'overdue', dueWithin2000: false };
        case 'dueSoon':
          return { ...base, statusTab: 'dueSoon', dueWithin2000: false };
        case 'dueWithin2000':
        case 'vehiclesRequiringService':
        default:
          return { ...base, statusTab: 'all', dueWithin2000: true };
      }
    });
  }, []);

  const baseForTabs = useMemo(
    () =>
      filterMaintenanceWorkItems(workItems, {
        priority: filters.priority,
        type: filters.type,
        vehicleSearch: filters.vehicleSearch,
        driverSearch: filters.driverSearch,
      }),
    [workItems, filters.priority, filters.type, filters.vehicleSearch, filters.driverSearch]
  );

  const activeTabCounts = useMemo(
    () => ({
      overdue: baseForTabs.filter((w) => w.dueStatus === 'overdue').length,
      dueSoon: baseForTabs.filter((w) => w.dueStatus === 'dueSoon').length,
      scheduled: baseForTabs.filter((w) => w.dueStatus === 'scheduled').length,
      future: baseForTabs.filter((w) => w.dueStatus === 'future').length,
      all: baseForTabs.length,
    }),
    [baseForTabs]
  );

  const filtered = useMemo(
    () => filterMaintenanceWorkItems(workItems, filters),
    [workItems, filters]
  );

  const sortedByStatus = useMemo(
    () => sortMaintenanceWorkItems(filtered, 'status'),
    [filtered]
  );
  const sortedByPriority = useMemo(
    () => sortMaintenanceWorkItems(filtered, 'priority'),
    [filtered]
  );

  const resultLabel = useMemo(() => {
    const n = filtered.length;
    const noun = n === 1 ? 'work item' : 'work items';
    if (filters.dueWithin2000) return `${n} ${noun} due within 2,000 km`;
    switch (filters.statusTab) {
      case 'overdue': return `${n} overdue ${noun}`;
      case 'dueSoon': return `${n} due-soon ${noun}`;
      case 'scheduled': return `${n} scheduled ${noun}`;
      case 'future': return `${n} future ${noun}`;
      default: return `${n} ${noun}`;
    }
  }, [filtered, filters]);

  const activeKpi = useMemo(() => {
    if (filters.dueWithin2000) return 'dueWithin2000';
    if (filters.statusTab === 'overdue') return 'overdue';
    if (filters.statusTab === 'dueSoon') return 'dueSoon';
    return null;
  }, [filters]);

  return useMemo(
    () => ({
      filters,
      setStatusTab,
      setPriority,
      setType,
      setVehicleSearch,
      setDriverSearch,
      applyKpiPreset,
      resetFilters,
      filtered,
      sortedByStatus,
      sortedByPriority,
      activeTabCounts,
      resultLabel,
      activeKpi,
    }),
    [
      filters,
      setStatusTab,
      setPriority,
      setType,
      setVehicleSearch,
      setDriverSearch,
      applyKpiPreset,
      resetFilters,
      filtered,
      sortedByStatus,
      sortedByPriority,
      activeTabCounts,
      resultLabel,
      activeKpi,
    ]
  );
}
