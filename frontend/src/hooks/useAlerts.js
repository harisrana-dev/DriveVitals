import { useMemo, useState, useCallback } from 'react';
import { useLiveData } from '../context/LiveDataContext';
import {
  deriveIncidents,
  deriveDrivingEvents,
  computeAlertKpis,
  computeSummaryDistribution,
  computeCategoryDistribution,
  buildAlertTimeline,
} from '../utils/alerts';

const ALERT_TYPE_LABELS = {
  engine_overheat: 'Engine Overheat',
  coolant_warning: 'Coolant Warning',
  fuel_critical: 'Fuel Critical',
  low_fuel: 'Low Fuel',
  health_critical: 'Health Critical',
  health_warning: 'Health Warning',
  high_engine_load: 'High Engine Load',
  harsh_braking: 'Harsh Braking',
  aggressive_throttle: 'Aggressive Throttle',
  high_rpm: 'High RPM',
  speeding: 'Speeding',
};

const ALERT_TYPE_CATEGORY = {
  engine_overheat: 'Cooling',
  coolant_warning: 'Cooling',
  fuel_critical: 'Fuel',
  low_fuel: 'Fuel',
  health_critical: 'Electrical',
  health_warning: 'Electrical',
  high_engine_load: 'Engine',
  harsh_braking: 'Driving',
  aggressive_throttle: 'Driving',
  high_rpm: 'Driving',
  speeding: 'Driving',
};

function titleCase(value) {
  if (!value) return 'Alert';
  return String(value).replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

function normalizeSeverity(sev) {
  const s = String(sev || 'warning').toLowerCase();
  if (s === 'critical' || s === 'warning' || s === 'info') return s;
  return 'warning';
}

function mapRestAlert(a, meta) {
  return {
    id: a.alert_id,
    alert_id: a.alert_id,
    vehicle_id: a.vehicle_id,
    vehicle_name: meta?.vehicle_name || a.vehicle_id,
    driver_name: meta?.driver_name || a.driver_id || '—',
    event_type: a.alert_type,
    eventType: ALERT_TYPE_LABELS[a.alert_type] || titleCase(a.alert_type),
    severity: normalizeSeverity(a.severity),
    category: ALERT_TYPE_CATEGORY[a.alert_type] || 'Engine',
    status: a.status === 'resolved' ? 'resolved' : 'active',
    acknowledged: !!a.acknowledged,
    started_at: a.created_at || new Date().toISOString(),
    resolved_at: a.resolved_at || null,
    description: titleCase(a.alert_type),
    speed: 0,
    rpm: 0,
    throttle_position_percent: 0,
    brake_pressure: 0,
    engine_load_percent: 0,
    fuel_level_percent: 0,
    coolant_temperature_c: 0,
    overall_health_score: meta?.overall_health_score ?? 100,
  };
}

function mapRestAlerts(alerts, fleetMeta) {
  if (!Array.isArray(alerts)) return [];
  return alerts.map((a) => mapRestAlert(a, fleetMeta?.[a.vehicle_id]));
}

export function useAlerts() {
  const { dashboard, alerts: restAlerts, fleetMeta } = useLiveData();
  const vehicles = dashboard?.vehicles;

  const incidents = useMemo(() => {
    const fresh = deriveIncidents(vehicles).map((inc) => ({
      ...inc,
      started_at: inc.started_at || new Date().toISOString(),
    }));
    return [...fresh, ...mapRestAlerts(restAlerts, fleetMeta)];
  }, [vehicles, restAlerts, fleetMeta]);

  const drivingEvents = useMemo(() => deriveDrivingEvents(vehicles), [vehicles]);

  return useMemo(
    () => ({
      incidents,
      drivingEvents,
      kpis: computeAlertKpis(incidents),
      distribution: computeSummaryDistribution(incidents),
      categoryDist: computeCategoryDistribution(incidents),
      timeline: buildAlertTimeline(incidents),
    }),
    [incidents, drivingEvents]
  );
}

export function useAlert(alertId) {
  const { incidents } = useAlerts();
  return useMemo(() => incidents.find((a) => a.id === alertId) || null, [incidents, alertId]);
}

export function useAlertFilters() {
  const [filters, setFilters] = useState({
    severity: 'all',
    category: 'all',
    vehicleSearch: '',
    driverSearch: '',
    timeRange: 'live',
  });

  const setSeverity = useCallback((v) => setFilters((f) => ({ ...f, severity: v })), []);
  const setCategory = useCallback((v) => setFilters((f) => ({ ...f, category: v })), []);
  const setVehicleSearch = useCallback((v) => setFilters((f) => ({ ...f, vehicleSearch: v })), []);
  const setDriverSearch = useCallback((v) => setFilters((f) => ({ ...f, driverSearch: v })), []);
  const setTimeRange = useCallback((v) => setFilters((f) => ({ ...f, timeRange: v })), []);

  const { incidents } = useAlerts();

  const filtered = useMemo(() => {
    let result = incidents;

    if (filters.severity !== 'all') {
      result = result.filter((a) => a.severity === filters.severity);
    }

    if (filters.category !== 'all') {
      result = result.filter((a) => a.category === filters.category);
    }

    if (filters.vehicleSearch) {
      const search = filters.vehicleSearch.toLowerCase();
      result = result.filter((a) =>
        a.vehicle_name?.toLowerCase().includes(search) || a.vehicle_id?.toLowerCase().includes(search)
      );
    }

    if (filters.driverSearch) {
      const search = filters.driverSearch.toLowerCase();
      result = result.filter((a) => a.driver_name?.toLowerCase().includes(search));
    }

    if (filters.timeRange === 'live') {
      result = result.filter((a) => a.status === 'active');
    }

    return result;
  }, [incidents, filters]);

  return {
    filters,
    setSeverity,
    setCategory,
    setVehicleSearch,
    setDriverSearch,
    setTimeRange,
    filteredAlerts: filtered,
    totalAlerts: incidents,
  };
}
