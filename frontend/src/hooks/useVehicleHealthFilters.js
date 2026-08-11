import { useMemo, useState } from 'react';
import { useVehicleHealth } from './useVehicleHealth';

export function useVehicleHealthFilters() {
  const { vehicles, fleetStats } = useVehicleHealth();

  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [minScore, setMinScore] = useState('');
  const [maxScore, setMaxScore] = useState('');
  const [sortBy, setSortBy] = useState('name');
  const [sortAsc, setSortAsc] = useState(true);

  const filtered = useMemo(() => {
    let result = vehicles || [];
    const q = search.trim().toLowerCase();
    if (q) {
      result = result.filter(
        (v) =>
          v.name.toLowerCase().includes(q) ||
          v.id.toLowerCase().includes(q) ||
          (v.driverName || '').toLowerCase().includes(q) ||
          (v.driverId || '').toLowerCase().includes(q)
      );
    }

    if (statusFilter) {
      result = result.filter((v) => v.healthCategory === statusFilter);
    }

    const min = minScore === '' ? null : Number(minScore);
    const max = maxScore === '' ? null : Number(maxScore);
    if (min != null || max != null) {
      result = result.filter((v) => {
        if (v.overallHealth == null) return false;
        if (min != null && v.overallHealth < min) return false;
        if (max != null && v.overallHealth > max) return false;
        return true;
      });
    }

    result = [...result].sort((a, b) => {
      let cmp = 0;
      switch (sortBy) {
        case 'name':
          cmp = a.name.localeCompare(b.name);
          break;
        case 'overallHealth': {
          const av = a.overallHealth == null ? -1 : a.overallHealth;
          const bv = b.overallHealth == null ? -1 : b.overallHealth;
          cmp = av - bv;
          break;
        }
        case 'speed':
          cmp = (a.speed ?? -1) - (b.speed ?? -1);
          break;
        case 'rpm':
          cmp = (a.rpm ?? -1) - (b.rpm ?? -1);
          break;
        default:
          break;
      }
      return sortAsc ? cmp : -cmp;
    });

    return result;
  }, [vehicles, search, statusFilter, minScore, maxScore, sortBy, sortAsc]);

  const hasActiveFilters =
    search.trim() !== '' ||
    statusFilter !== '' ||
    minScore !== '' ||
    maxScore !== '' ||
    sortBy !== 'name';

  const reset = () => {
    setSearch('');
    setStatusFilter('');
    setMinScore('');
    setMaxScore('');
    setSortBy('name');
    setSortAsc(true);
  };

  return {
    vehicles: filtered,
    fleetStats,
    totalCount: (vehicles || []).length,
    search,
    setSearch,
    statusFilter,
    setStatusFilter,
    minScore,
    setMinScore,
    maxScore,
    setMaxScore,
    sortBy,
    setSortBy,
    sortAsc,
    setSortAsc,
    toggleSort: () => setSortAsc((prev) => !prev),
    hasActiveFilters,
    reset,
  };
}
