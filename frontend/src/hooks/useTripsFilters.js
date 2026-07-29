import { useMemo, useState } from 'react';
import { useTrips } from './useTripsData';

export function useTripsFilters() {
  const trips = useTrips();

  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [routeFilter, setRouteFilter] = useState('');
  const [sortBy, setSortBy] = useState('date');
  const [sortAsc, setSortAsc] = useState(false);

  const filtered = useMemo(() => {
    let result = [...(trips || [])];

    if (search.trim()) {
      const q = search.toLowerCase();
      result = result.filter(
        (t) =>
          t.vehicleName.toLowerCase().includes(q) ||
          t.vehicleId.toLowerCase().includes(q) ||
          t.driverName.toLowerCase().includes(q) ||
          t.driverId?.toLowerCase().includes(q) ||
          t.id.toLowerCase().includes(q)
      );
    }

    if (statusFilter) {
      result = result.filter((t) => {
        if (statusFilter === 'completed') return t.completedAt != null;
        if (statusFilter === 'running') return t.completedAt == null;
        return true;
      });
    }

    if (routeFilter) {
      result = result.filter((t) => t.routeType === routeFilter);
    }

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
        default:
          cmp = 0;
      }
      return sortAsc ? cmp : -cmp;
    });

    return result;
  }, [trips, search, statusFilter, routeFilter, sortBy, sortAsc]);

  return {
    trips: filtered,
    search,
    setSearch,
    statusFilter,
    setStatusFilter,
    routeFilter,
    setRouteFilter,
    sortBy,
    setSortBy,
    sortAsc,
    setSortAsc,
    toggleSort: () => setSortAsc((prev) => !prev),
  };
}
