import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useTrips } from './useTripsData';
import { listTrips } from '../services/api/tripApi';
import { mapTrips } from '../utils/trips';
import {
  buildTripQuery,
  computeTripSummary,
  matchesTripSearch,
  refineTrips,
  sortTrips,
} from '../utils/tripFilters';

const INITIAL_STATE = {
  items: [],
  count: 0,
  offset: 0,
  initialLoading: true,
  loadingMore: false,
  error: null,
};

export function useTripsFilters() {
  const liveTrips = useTrips();

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

  const [history, setHistory] = useState(INITIAL_STATE);
  const [refreshIndex, setRefreshIndex] = useState(0);

  const historyRef = useRef(history);
  useEffect(() => {
    historyRef.current = history;
  }, [history]);

  const requestSeq = useRef(0);

  const serverQuery = useMemo(
    () => buildTripQuery({ statusFilter, routeFilter, driverFilter, vehicleFilter }),
    [statusFilter, routeFilter, driverFilter, vehicleFilter]
  );

  useEffect(() => {
    const seq = ++requestSeq.current;
    setHistory((prev) => ({
      ...prev,
      items: [],
      count: 0,
      offset: 0,
      initialLoading: true,
      loadingMore: false,
      error: null,
    }));

    listTrips({ ...serverQuery, offset: 0 })
      .then((res) => {
        if (requestSeq.current !== seq) return;
        const data = mapTrips(res?.data);
        setHistory({
          items: data,
          count: typeof res?.count === 'number' ? res.count : data.length,
          offset: data.length,
          initialLoading: false,
          loadingMore: false,
          error: null,
        });
      })
      .catch((err) => {
        if (requestSeq.current !== seq) return;
        setHistory((prev) => ({ ...prev, initialLoading: false, error: err }));
      });
  }, [serverQuery, refreshIndex]);

  const loadMoreTrips = useCallback(async () => {
    const current = historyRef.current;
    if (current.initialLoading || current.loadingMore) return;
    if (current.offset >= current.count) return;

    const seq = requestSeq.current;
    setHistory((prev) => ({ ...prev, loadingMore: true }));

    try {
      const res = await listTrips({ ...serverQuery, offset: current.offset });
      if (requestSeq.current !== seq) return;
      const data = mapTrips(res?.data);
      setHistory((prev) => {
        const seen = new Set(prev.items.map((t) => t.id));
        const fresh = data.filter((t) => t && !seen.has(t.id));
        return {
          items: [...prev.items, ...fresh],
          count: typeof res?.count === 'number' ? res.count : prev.count,
          offset: prev.offset + data.length,
          initialLoading: false,
          loadingMore: false,
          error: null,
        };
      });
    } catch (err) {
      if (requestSeq.current !== seq) return;
      setHistory((prev) => ({ ...prev, loadingMore: false, error: err }));
    }
  }, [serverQuery]);

  const retryTrips = useCallback(() => {
    setRefreshIndex((i) => i + 1);
  }, []);

  const activeTrips = useMemo(
    () =>
      sortTrips(
        (liveTrips || []).filter(
          (t) => t.status === 'in_progress' && matchesTripSearch(t, search)
        ),
        sortBy,
        sortAsc
      ),
    [liveTrips, search, sortBy, sortAsc]
  );

  const historicalTrips = useMemo(
    () =>
      sortTrips(
        refineTrips(history.items, { search, gradeFilter, dateFrom, dateTo }),
        sortBy,
        sortAsc
      ),
    [history.items, search, gradeFilter, dateFrom, dateTo, sortBy, sortAsc]
  );

  const driverOptions = useMemo(() => {
    const seen = new Map();
    [...history.items, ...(liveTrips || [])].forEach((t) => {
      if (t.driverId && !seen.has(t.driverId)) {
        seen.set(t.driverId, t.driverName || t.driverId);
      }
    });
    return Array.from(seen, ([value, label]) => ({ value, label }));
  }, [history.items, liveTrips]);

  const vehicleOptions = useMemo(() => {
    const seen = new Map();
    [...history.items, ...(liveTrips || [])].forEach((t) => {
      if (t.vehicleId && !seen.has(t.vehicleId)) {
        seen.set(t.vehicleId, t.vehicleName || t.vehicleId);
      }
    });
    return Array.from(seen, ([value, label]) => ({ value, label }));
  }, [history.items, liveTrips]);

  const summary = useMemo(() => {
    const seen = new Set();
    const all = [];
    [...history.items, ...(liveTrips || [])].forEach((t) => {
      if (t && t.id && !seen.has(t.id)) {
        seen.add(t.id);
        all.push(t);
      }
    });
    return computeTripSummary(all);
  }, [history.items, liveTrips]);

  const toggleSort = useCallback(() => setSortAsc((prev) => !prev), []);

  const resetFilters = useCallback(() => {
    setSearch('');
    setStatusFilter('');
    setRouteFilter('');
    setDriverFilter('');
    setVehicleFilter('');
    setGradeFilter('');
    setDateFrom('');
    setDateTo('');
  }, []);

  return {
    activeTrips,
    historicalTrips,
    liveTrips,
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
    toggleSort,
    resetFilters,
    loadMoreTrips,
    retryTrips,
    summary,
    historyCount: history.count,
    historyLoaded: history.items.length,
    historyError: history.error,
    historyLoading: history.initialLoading,
    historyLoadingMore: history.loadingMore,
    historyHasMore: history.items.length < history.count,
  };
}
