import { useMemo, useState } from 'react';
import { useVehicles } from './useFleetData';

export function useFleetFilters() {
  const vehicles = useVehicles();

  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [sortBy, setSortBy] = useState('name');
  const [sortAsc, setSortAsc] = useState(true);

  const filtered = useMemo(() => {
    let result = [...(vehicles || [])];

    if (search.trim()) {
      const q = search.toLowerCase();
      result = result.filter(
        (v) =>
          v.name.toLowerCase().includes(q) ||
          v.id.toLowerCase().includes(q) ||
          v.driver.toLowerCase().includes(q) ||
          v.driverId?.toLowerCase().includes(q)
      );
    }

    if (statusFilter) {
      result = result.filter((v) => {
        if (statusFilter === 'alert') return v.alertCount > 0;
        return v.status === statusFilter;
      });
    }

    result.sort((a, b) => {
      let cmp = 0;
      switch (sortBy) {
        case 'name':
          cmp = a.name.localeCompare(b.name);
          break;
        case 'speed':
          cmp = a.speed - b.speed;
          break;
        case 'healthScore':
          cmp = a.healthScore - b.healthScore;
          break;
        case 'fuelLevel':
          cmp = a.fuelLevel - b.fuelLevel;
          break;
        default:
          cmp = 0;
      }
      return sortAsc ? cmp : -cmp;
    });

    return result;
  }, [vehicles, search, statusFilter, sortBy, sortAsc]);

  return {
    vehicles: filtered,
    search,
    setSearch,
    statusFilter,
    setStatusFilter,
    sortBy,
    setSortBy,
    sortAsc,
    setSortAsc,
    toggleSort: () => setSortAsc((prev) => !prev),
  };
}
