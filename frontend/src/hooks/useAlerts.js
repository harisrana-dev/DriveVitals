import { useMemo, useState, useCallback, useRef } from 'react';
import { useFleetContext } from '../context/FleetContext';
import {
  deriveIncidents,
  deriveDrivingEvents,
  computeAlertKpis,
  computeSummaryDistribution,
  computeCategoryDistribution,
  buildAlertTimeline,
} from '../utils/alerts';

let nextEventId = 0;

export function useAlerts() {
  const { dashboard } = useFleetContext();
  const incidentsRef = useRef([]);
  const timelineRef = useRef([]);

  return useMemo(() => {
    const vehicles = dashboard?.vehicles;
    const freshIncidents = deriveIncidents(vehicles);
    const drivingEvents = deriveDrivingEvents(vehicles);

    const existing = new Map(incidentsRef.current.map((i) => [i.id, i]));
    const merged = [];

    for (const inc of freshIncidents) {
      if (existing.has(inc.id)) {
        merged.push({ ...existing.get(inc.id), ...inc, id: inc.id });
      } else {
        merged.push({ ...inc, started_at: new Date().toISOString(), status: 'active' });
      }
    }

    incidentsRef.current = merged;

    const prevTimeline = timelineRef.current;
    const existingTimelineIds = new Set(prevTimeline.map((t) => t.id));
    const newEvents = [];

    for (const evt of drivingEvents) {
      evt.id = evt.id || `evt-${nextEventId++}`;
      if (!existingTimelineIds.has(evt.id)) {
        newEvents.push(evt);
      }
    }

    const timeline = [...newEvents, ...prevTimeline].slice(0, 30);
    timelineRef.current = timeline;

    return {
      incidents: merged,
      drivingEvents: timeline,
      kpis: computeAlertKpis(merged, timeline),
      distribution: computeSummaryDistribution(merged),
      categoryDist: computeCategoryDistribution(merged),
      timeline: buildAlertTimeline(merged),
    };
  }, [dashboard]);
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
