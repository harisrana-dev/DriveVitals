import { useMemo, useState } from 'react';
import { useLiveData } from '../context/LiveDataContext';
import { adaptDrivers, buildDriverRankings as buildRankingList } from '../services/driverAdapter';
import { computeTrend } from '../utils/trend';

const scoreCache = {};

function trendDirection(direction) {
  if (direction === 'up') return 'improving';
  if (direction === 'down' || direction === 'warning') return 'declining';
  return 'stable';
}

function applyDriverTrends(mapped) {
  for (const d of mapped) {
    const prev = scoreCache[d.id];
    const trend = computeTrend(d.safetyScore, prev?.score);
    if (trend) {
      d.trend = trendDirection(trend.direction);
      d.scoreDelta = trend.delta;
      d.scoreTrend = trend;
    } else {
      d.trend = 'stable';
      d.scoreDelta = 0;
      d.scoreTrend = null;
    }
    scoreCache[d.id] = { score: d.safetyScore };
  }
  return mapped;
}

export function useDrivers() {
  const { drivers, driverStatistics, dashboard } = useLiveData();

  return useMemo(
    () => applyDriverTrends(adaptDrivers(drivers, driverStatistics, dashboard?.vehicles)),
    [drivers, driverStatistics, dashboard]
  );
}

export function useDriver(id) {
  const drivers = useDrivers();
  return useMemo(() => drivers.find((d) => d.id === id) || null, [drivers, id]);
}

export function useDriverPerformance() {
  return null;
}

export function useDriverRanking() {
  const drivers = useDrivers();
  return useMemo(() => buildRankingList(drivers), [drivers]);
}

export function useDriversOverview() {
  const drivers = useDrivers();
  return useMemo(() => {
    const total = drivers.length;
    const active = drivers.filter((d) => d.status === 'active').length;
    const highRisk = drivers.filter((d) => d.riskLevel === 'high' || d.riskLevel === 'critical').length;
    const avgScore = total > 0
      ? Math.round(drivers.reduce((s, d) => s + d.safetyScore, 0) / total)
      : 0;
    return { total, active, highRisk, avgScore };
  }, [drivers]);
}

export function useDriversFilters() {
  const drivers = useDrivers();

  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [riskFilter, setRiskFilter] = useState('');

  const filtered = useMemo(() => {
    let result = [...drivers];
    if (search.trim()) {
      const q = search.toLowerCase();
      result = result.filter(
        (d) =>
          d.name.toLowerCase().includes(q) ||
          d.id.toLowerCase().includes(q) ||
          d.vehicleName?.toLowerCase().includes(q) ||
          d.vehicleId?.toLowerCase().includes(q)
      );
    }
    if (statusFilter) {
      result = result.filter((d) => d.status === statusFilter);
    }
    if (riskFilter) {
      result = result.filter((d) => d.riskLevel === riskFilter);
    }
    return result;
  }, [drivers, search, statusFilter, riskFilter]);

  return {
    drivers: filtered,
    search,
    setSearch,
    statusFilter,
    setStatusFilter,
    riskFilter,
    setRiskFilter,
  };
}
