import { useMemo, useState } from 'react';
import { useTrips } from './useTripsData';

export function useTripsFilters() {
  const trips = useTrips();

  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [routeFilter, setRouteFilter] = useState('');
  const [driverFilter, setDriverFilter] = useState('');
  const [vehicleFilter, setVehicleFilter] = useState('');
  const [gradeFilter, setGradeFilter] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [sortBy, setSortBy] = useState('date');
  const [sortAsc, setSortAsc] = useState(false);

  const driverOptions = useMemo(() => {
    const seen = new Map();
    (trips || []).forEach((t) => {
      if (t.driverId && !seen.has(t.driverId)) {
        seen.set(t.driverId, t.driverName);
      }
    });
    return Array.from(seen, ([value, label]) => ({ value, label }));
  }, [trips]);

  const vehicleOptions = useMemo(() => {
    const seen = new Map();
    (trips || []).forEach((t) => {
      if (t.vehicleId && !seen.has(t.vehicleId)) {
        seen.set(t.vehicleId, t.vehicleName);
      }
    });
    return Array.from(seen, ([value, label]) => ({ value, label }));
  }, [trips]);

  const applySearch = useMemo(() => (list) => {
    if (!search.trim()) return list;
    const q = search.toLowerCase();
    return list.filter(
      (t) =>
        t.vehicleName.toLowerCase().includes(q) ||
        t.vehicleId.toLowerCase().includes(q) ||
        t.driverName.toLowerCase().includes(q) ||
        t.driverId?.toLowerCase().includes(q) ||
        t.id.toLowerCase().includes(q) ||
        (t.routeName || '').toLowerCase().includes(q)
    );
  }, [search]);

  const sortTrips = useMemo(() => (list) => {
    const result = [...list];
    result.sort((a, b) => {
      let cmp = 0;
      switch (sortBy) {
        case 'date':
          cmp = (a.completedAt || a.startedAt || '').localeCompare(b.completedAt || b.startedAt || '');
          break;
        case 'distance':
          cmp = a.distance - b.distance;
          break;
        case 'score':
          cmp = a.safetyScore - b.safetyScore;
          break;
        case 'fuel':
          cmp = a.fuelConsumed - b.fuelConsumed;
          break;
      }
      return sortAsc ? cmp : -cmp;
    });
    return result;
  }, [sortBy, sortAsc]);

  const activeTrips = useMemo(
    () => sortTrips(applySearch((trips || []).filter((t) => t.status === 'in_progress'))),
    [trips, applySearch, sortTrips]
  );

  const completedTrips = useMemo(() => {
    let result = (trips || []).filter((t) => t.completedAt != null);

    if (driverFilter) {
      result = result.filter((t) => t.driverId === driverFilter);
    }
    if (vehicleFilter) {
      result = result.filter((t) => t.vehicleId === vehicleFilter);
    }
    if (gradeFilter) {
      result = result.filter((t) => t.grade === gradeFilter);
    }
    if (dateFrom) {
      const from = new Date(`${dateFrom}T00:00:00`).getTime();
      result = result.filter((t) => {
        const ts = new Date(t.completedAt || t.startedAt).getTime();
        return !Number.isNaN(ts) && ts >= from;
      });
    }
    if (dateTo) {
      const to = new Date(`${dateTo}T23:59:59.999`).getTime();
      result = result.filter((t) => {
        const ts = new Date(t.completedAt || t.startedAt).getTime();
        return !Number.isNaN(ts) && ts <= to;
      });
    }
    if (statusFilter === 'running') return [];

    if (routeFilter) {
      result = result.filter((t) => t.routeType === routeFilter);
    }

    return sortTrips(applySearch(result));
  }, [
    trips,
    statusFilter,
    routeFilter,
    driverFilter,
    vehicleFilter,
    gradeFilter,
    dateFrom,
    dateTo,
    applySearch,
    sortTrips,
  ]);

  const resetFilters = () => {
    setSearch('');
    setStatusFilter('');
    setRouteFilter('');
    setDriverFilter('');
    setVehicleFilter('');
    setGradeFilter('');
    setDateFrom('');
    setDateTo('');
  };

  return {
    activeTrips,
    completedTrips,
    search,
    setSearch,
    statusFilter,
    setStatusFilter,
    routeFilter,
    setRouteFilter,
    driverFilter,
    setDriverFilter,
    driverOptions,
    vehicleFilter,
    setVehicleFilter,
    vehicleOptions,
    gradeFilter,
    setGradeFilter,
    dateFrom,
    setDateFrom,
    dateTo,
    setDateTo,
    sortBy,
    setSortBy,
    sortAsc,
    setSortAsc,
    toggleSort: () => setSortAsc((prev) => !prev),
    resetFilters,
  };
}
