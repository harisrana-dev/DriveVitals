import { useMemo, useState } from 'react';
import { useLiveData } from '../context/useLiveData';
import {
  adaptDrivers,
  buildDriverRankings as buildRankingList,
  driverRiskLevel,
} from '../services/driverAdapter';
import { computeDriverTrend } from '../utils/driverTrend';
import { mapTrips } from '../utils/trips';

function applyDriverTrends(mapped) {
  return mapped.map((d) => {
    const trend = computeDriverTrend(d.historical.performanceHistory);
    if (trend) {
      return {
        ...d,
        historical: {
          ...d.historical,
          trend: trend.direction,
          scoreDelta: trend.delta,
          scoreTrend: trend,
        },
      };
    }
    return d;
  });
}

function applyDriverPercentiles(drivers) {
  const scored = drivers.filter(
    (d) => d.historical?.safetyScore != null && d.historical?.scoreQuality === 'valid'
  );
  if (scored.length < 2) return drivers;
  const sorted = [...scored].sort(
    (a, b) => a.historical.safetyScore - b.historical.safetyScore
  );
  const uniqueScores = new Set(sorted.map((d) => d.historical.safetyScore));
  const hasMeaningfulVariation = uniqueScores.size > 1;

  return drivers.map((d) => {
    if (d.historical?.safetyScore == null || d.historical?.scoreQuality !== 'valid') return d;
    if (!hasMeaningfulVariation) {
      return { ...d, historical: { ...d.historical, percentile: null, percentileNote: 'no_variation' } };
    }
    const percentile = Math.round(
      (sorted.filter((x) => x.historical.safetyScore <= d.historical.safetyScore).length /
        sorted.length) *
        100
    );
    return { ...d, historical: { ...d.historical, percentile } };
  });
}

export function useDrivers() {
  const { drivers, driverStatistics, dashboard, trips } = useLiveData();

  return useMemo(() => {
    const mappedTrips = mapTrips(trips?.trips);
    const adapted = adaptDrivers(
      drivers,
      driverStatistics,
      dashboard?.vehicles,
      mappedTrips
    );
    return applyDriverPercentiles(applyDriverTrends(adapted));
  }, [drivers, driverStatistics, dashboard, trips]);
}

export function useDriver(id) {
  const drivers = useDrivers();
  return useMemo(() => drivers.find((d) => d.id === id) || null, [drivers, id]);
}

export function useDriverPerformance(driverId) {
  const driver = useDriver(driverId);
  return useMemo(() => {
    if (!driver || driver.historical.performanceHistory.length < 2) return null;
    return {
      history: driver.historical.performanceHistory.map((t) => ({
        score: t.safetyScore,
        date: t.completedAt || null,
        routeId: t.routeId || null,
      })),
    };
  }, [driver]);
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
    const highRisk = drivers.filter(
      (d) => {
        const level = driverRiskLevel(d);
        return level === 'high' || level === 'critical';
      }
    ).length;
    const scored = drivers.filter(
      (d) => d.historical?.safetyScore != null && d.historical?.scoreQuality === 'valid'
    );
    const avgScore =
      scored.length > 0
        ? Math.round(scored.reduce((s, d) => s + d.historical.safetyScore, 0) / scored.length)
        : null;
    return { total, active, highRisk, avgScore };
  }, [drivers]);
}

export function useDriversFilters() {
  const drivers = useDrivers();

  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [riskFilter, setRiskFilter] = useState('');
  const [performanceFilter, setPerformanceFilter] = useState('');

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
      result = result.filter((d) => driverRiskLevel(d) === riskFilter);
    }
    if (performanceFilter === 'no_score') {
      result = result.filter((d) => d.historical?.safetyScore == null);
    } else if (performanceFilter) {
      result = result.filter((d) => d.historical?.trend === performanceFilter);
    }
    return result;
  }, [drivers, search, statusFilter, riskFilter, performanceFilter]);

  return {
    drivers: filtered,
    totalCount: drivers.length,
    hasActiveFilters: !!(search || statusFilter || riskFilter || performanceFilter),
    search,
    setSearch,
    statusFilter,
    setStatusFilter,
    riskFilter,
    setRiskFilter,
    performanceFilter,
    setPerformanceFilter,
  };
}
