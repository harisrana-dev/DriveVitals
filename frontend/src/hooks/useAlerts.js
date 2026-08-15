import { useMemo, useState, useCallback } from 'react';
import { useLiveData } from '../context/LiveDataContext';
import { adaptAlerts, severityRank } from '../services/alertAdapter';
import {
  computeAlertKpis,
  computeActiveSeverityDistribution,
  computeActiveCategoryDistribution,
  computeVehicleRisk,
  computeInsights,
  groupAlertsIntoIncidents,
  filterAlertsByTimeRange,
  withinHours,
  severityLabel,
} from '../utils/alerts';

const LIVE_EVENT_LABELS = {
  harsh_braking: 'Harsh Braking',
  aggressive_throttle: 'Aggressive Throttle',
  high_rpm: 'High RPM',
  speeding: 'Speeding',
};

function titleCase(value) {
  if (!value) return 'Event';
  return String(value).replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

/**
 * Live driving events are read directly from the backend dashboard
 * snapshot's ``active_event_types`` for each vehicle. No event is ever
 * synthesised on the client: no fabricated timestamps, ids or events.
 * The key is a stable ``vehicle:event_type`` pair (not a timestamp).
 */
function buildLiveEvents(vehicles) {
  if (!Array.isArray(vehicles)) return [];
  const events = [];
  for (const v of vehicles) {
    const types = v.active_event_types || [];
    for (const eventType of types) {
      events.push({
        id: `${v.vehicle_id}:${eventType}`,
        vehicle_id: v.vehicle_id,
        vehicle_name: v.vehicle_name || v.vehicle_id,
        driver_name: v.driver_name || null,
        event_type: eventType,
        label: LIVE_EVENT_LABELS[eventType] || titleCase(eventType),
      });
    }
  }
  return events;
}

/**
 * Canonical Alerts hook. Every consumer on the Alerts page derives from
 * the same adapted rows and selectors so all counts reconcile.
 */
export function useAlerts() {
  const { alerts: restAlerts, fleetMeta } = useLiveData();

  const alerts = useMemo(
    () => adaptAlerts(restAlerts, fleetMeta),
    [restAlerts, fleetMeta]
  );

  const sorted = useMemo(
    () =>
      [...alerts].sort((a, b) => {
        const rank = severityRank(a.severity) - severityRank(b.severity);
        if (rank !== 0) return rank;
        return (
          (new Date(b.created_at).getTime() || 0) -
          (new Date(a.created_at).getTime() || 0)
        );
      }),
    [alerts]
  );

  return useMemo(
    () => {
      const incidents = groupAlertsIntoIncidents(sorted);
      return {
        alerts: sorted,
        incidents,
        kpis: computeAlertKpis(sorted),
        activeSeverityDist: computeActiveSeverityDistribution(sorted),
        categoryDist: computeActiveCategoryDistribution(sorted),
        vehicleRisk: computeVehicleRisk(sorted),
        insights: computeInsights(sorted),
      };
    },
    [sorted]
  );
}

/**
 * Live presence, isolated from persisted-alert derived data. The band is
 * the only consumer; a dashboard snapshot can change LIVE NOW without
 * churning the KPI/queue/intelligence/history selectors returned above.
 */
export function useLiveEvents() {
  const { dashboard } = useLiveData();
  const vehicles = dashboard?.vehicles;
  return useMemo(() => buildLiveEvents(vehicles), [vehicles]);
}

export function useAlert(alertId) {
  const { alerts } = useAlerts();
  return useMemo(
    () => alerts.find((a) => a.alert_id === alertId) || null,
    [alerts, alertId]
  );
}

function applyBaseFilters(alerts, filters) {
  let result = filterAlertsByTimeRange(alerts, filters.timeRange);

  if (filters.severity !== 'all') {
    result = result.filter((a) => a.severity === filters.severity);
  }

  if (filters.category === '__unclassified__') {
    result = result.filter((a) => a.category == null);
  } else if (filters.category !== 'all') {
    result = result.filter((a) => a.category === filters.category);
  }

  if (filters.vehicleSearch) {
    const search = filters.vehicleSearch.toLowerCase();
    result = result.filter(
      (a) =>
        a.vehicle_name?.toLowerCase().includes(search) ||
        a.vehicle_id?.toLowerCase().includes(search)
    );
  }

  if (filters.driverSearch) {
    const search = filters.driverSearch.toLowerCase();
    result = result.filter((a) => a.driver_name?.toLowerCase().includes(search));
  }

  return result;
}

function applyStatusFilters(list, filters) {
  let result = list;
  if (filters.statusTab === 'active') {
    result = result.filter((a) => a.status === 'active');
  } else if (filters.statusTab === 'acknowledged') {
    result = result.filter((a) => a.status === 'active' && a.acknowledged);
  } else if (filters.statusTab === 'resolved') {
    result = result.filter((a) => a.status === 'resolved');
  }

  if (filters.unacknowledgedOnly) {
    result = result.filter((a) => a.status === 'active' && !a.acknowledged);
  }
  if (filters.resolvedWithinH) {
    result = result.filter(
      (a) => a.status === 'resolved' && withinHours(a.resolved_at, filters.resolvedWithinH)
    );
  }
  return result;
}

function describeResult(count, filters) {
  const plural = count === 1 ? 'alert' : 'alerts';
  if (filters.resolvedWithinH) {
    return `${count} resolved ${plural} (last ${filters.resolvedWithinH}h)`;
  }
  if (filters.unacknowledgedOnly) {
    return `${count} unacknowledged ${plural}`;
  }
  const sev = filters.severity !== 'all' ? severityLabel(filters.severity)?.toLowerCase() : null;
  switch (filters.statusTab) {
    case 'active':
      return sev ? `${count} ${sev} ${plural}` : `${count} active ${plural}`;
    case 'acknowledged':
      return `${count} acknowledged ${plural}`;
    case 'resolved':
      return `${count} resolved ${plural}`;
    default:
      return sev ? `${count} ${sev} ${plural}` : `${count} ${plural}`;
  }
}

/**
 * Full filter API for the Alerts page. The state lives here and is lifted
 * to the page so the KPI strip, tabs, filters bar and table all share one
 * source of truth (the previous per-component hook instances did not).
 */
export function useAlertFilters() {
  const [filters, setFilters] = useState({
    severity: 'all',
    category: 'all',
    vehicleSearch: '',
    driverSearch: '',
    timeRange: 'all',
    statusTab: 'active',
    unacknowledgedOnly: false,
    resolvedWithinH: null,
  });

  const setSeverity = useCallback((v) => setFilters((f) => ({ ...f, severity: v })), []);
  const setCategory = useCallback((v) => setFilters((f) => ({ ...f, category: v })), []);
  const setVehicleSearch = useCallback((v) => setFilters((f) => ({ ...f, vehicleSearch: v })), []);
  const setDriverSearch = useCallback((v) => setFilters((f) => ({ ...f, driverSearch: v })), []);
  const setTimeRange = useCallback((v) => setFilters((f) => ({ ...f, timeRange: v })), []);
  const setStatusTab = useCallback((v) => setFilters((f) => ({ ...f, statusTab: v })), []);

  const { alerts } = useAlerts();

  /**
   * Clicking a KPI navigates the history table to the matching population.
   * Presets reset the time range so the window is the full dataset.
   */
  const applyKpiPreset = useCallback((key) => {
    setFilters((f) => {
      const base = { ...f, timeRange: 'all', unacknowledgedOnly: false, resolvedWithinH: null };
      switch (key) {
        case 'critical':
          return { ...base, statusTab: 'active', severity: 'critical' };
        case 'high':
          return { ...base, statusTab: 'active', severity: 'high' };
        case 'unacknowledged':
          return { ...base, statusTab: 'active', severity: 'all', unacknowledgedOnly: true };
        case 'resolved24h':
          return { ...base, statusTab: 'resolved', severity: 'all', resolvedWithinH: 24 };
        case 'active':
        default:
          return { ...base, statusTab: 'active', severity: 'all' };
      }
    });
  }, []);

  const filtered = useMemo(
    () => applyStatusFilters(applyBaseFilters(alerts, filters), filters),
    [alerts, filters]
  );

  const filteredIncidents = useMemo(
    () => groupAlertsIntoIncidents(filtered),
    [filtered]
  );

  const baseForTabs = useMemo(
    () => applyBaseFilters(alerts, filters),
    [alerts, filters]
  );

  const activeTabCounts = useMemo(
    () => ({
      active: baseForTabs.filter((a) => a.status === 'active').length,
      acknowledged: baseForTabs.filter((a) => a.status === 'active' && a.acknowledged).length,
      resolved: baseForTabs.filter((a) => a.status === 'resolved').length,
      all: baseForTabs.length,
    }),
    [baseForTabs]
  );

  const resultLabel = useMemo(
    () => describeResult(filtered.length, filters),
    [filtered, filters]
  );

  const activeKpi = useMemo(() => {
    const f = filters;
    if (f.resolvedWithinH === 24 && f.statusTab === 'resolved') return 'resolved24h';
    if (f.statusTab === 'active' && f.unacknowledgedOnly) return 'unacknowledged';
    if (f.statusTab === 'active' && f.severity === 'critical') return 'critical';
    if (f.statusTab === 'active' && f.severity === 'high') return 'high';
    if (f.statusTab === 'active' && f.severity === 'all') return 'active';
    return null;
  }, [filters]);

  return useMemo(
    () => ({
      filters,
      setSeverity,
      setCategory,
      setVehicleSearch,
      setDriverSearch,
      setTimeRange,
      setStatusTab,
      applyKpiPreset,
      filteredIncidents,
      filteredAlerts: filtered,
      activeTabCounts,
      resultLabel,
      activeKpi,
    }),
    [
      filters,
      setSeverity,
      setCategory,
      setVehicleSearch,
      setDriverSearch,
      setTimeRange,
      setStatusTab,
      applyKpiPreset,
      filteredIncidents,
      filtered,
      activeTabCounts,
      resultLabel,
      activeKpi,
    ]
  );
}
