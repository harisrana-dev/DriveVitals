import { useMemo, useRef, useState } from 'react';
import { useFleetContext } from '../context/FleetContext';
import { adaptVehiclesToDrivers, buildDriverRankings as buildRankingList } from '../services/driverAdapter';
import { driverHistorical } from '../mocks/drivers';
import { computeTrend } from '../utils/trend';

export function useDrivers() {
  const { dashboard } = useFleetContext();
  const prevScoresRef = useRef({});

  return useMemo(() => {
    const live = adaptVehiclesToDrivers(dashboard?.vehicles);
    const drivers = live.length > 0 ? live : buildFallbackDrivers();

    const prev = prevScoresRef.current;

    for (const d of drivers) {
      const prevEntry = prev[d.id];
      const trend = computeTrend(d.safetyScore, prevEntry?.score);
      if (trend) {
        d.trend = trend.direction;
        d.scoreDelta = trend.delta;
        d.scoreTrend = trend;
      } else {
        d.trend = 'stable';
        d.scoreDelta = 0;
        d.scoreTrend = null;
      }
      prev[d.id] = { score: d.safetyScore, time: Date.now() };
    }

    return drivers;
  }, [dashboard]);
}

export function useDriver(id) {
  const drivers = useDrivers();
  return useMemo(() => drivers.find((d) => d.id === id) || null, [drivers, id]);
}

export function useDriverPerformance(driverId) {
  return useMemo(() => {
    const hist = driverHistorical[driverId];
    if (!hist) return null;
    return {
      history: hist.performanceHistory,
      breakdown: { braking: 0, acceleration: 0, speed: 0, efficiency: 0, overall: 0 },
      distribution: hist.behaviourDistribution,
    };
  }, [driverId]);
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

function buildFallbackDrivers() {
  return Object.entries(driverHistorical).map(([id, hist]) => ({
    id,
    name: id.replace('D-', 'Driver '),
    initials: id.replace('D-', 'D'),
    status: 'offline',
    riskLevel: 'low',
    behaviourState: 'stable',
    trend: 'stable',
    scoreDelta: 0,
    scoreTrend: null,
    vehicleId: '',
    vehicleName: '',
    safetyScore: 85,
    scoreBreakdown: { braking: 85, acceleration: 85, speed: 85, efficiency: 85, overall: 85 },
    activeEventTypes: [],
    speed: 0, rpm: 0, throttle: 0, brake: 0,
    fuelLevel: 0, engineLoad: 0, coolantTemp: 0, healthScore: 0,
    harshBraking: { count: 0, trend: 'stable', severity: 'none', active: false },
    aggressiveAcceleration: { count: 0, trend: 'stable', severity: 'none', active: false },
    overspeedEvents: { count: 0, trend: 'stable', severity: 'none', active: false },
    highRpmEvents: { count: 0, trend: 'stable', severity: 'none', active: false },
    lastActive: null,
    ...hist,
  }));
}
