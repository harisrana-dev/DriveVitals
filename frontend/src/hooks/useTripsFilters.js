import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useTrips } from './useTripsData';
import { useLiveData } from '../context/LiveDataContext';
import {
  deleteAbortedTrips,
  deleteTrip as deleteTripApi,
  listTrips,
} from '../services/api/tripApi';
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
  const { removeTrip } = useLiveData();

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
  const [deletedTripIds, setDeletedTripIds] = useState(() => new Set());
  const [abortedCount, setAbortedCount] = useState(0);

  const historyRef = useRef(history);
  useEffect(() => {
    historyRef.current = history;
  }, [history]);

  const liveTripsRef = useRef(liveTrips);
  useEffect(() => {
    liveTripsRef.current = liveTrips;
  }, [liveTrips]);

  const withoutDeleted = useCallback(
    (trips) => (trips || []).filter((t) => t && !deletedTripIds.has(t.id)),
    [deletedTripIds]
  );

  useEffect(() => {
    setDeletedTripIds((prev) => {
      if (prev.size === 0) return prev;
      const liveIds = new Set((liveTripsRef.current || []).map((t) => t.id));
      let changed = false;
      const next = new Set();
      prev.forEach((id) => {
        if (liveIds.has(id)) {
          next.add(id);
        } else {
          changed = true;
        }
      });
      return changed ? next : prev;
    });
  }, [liveTrips]);

  const refreshAbortedCount = useCallback(async () => {
    try {
      const res = await listTrips({ status: 'aborted', limit: 1, offset: 0 });
      setAbortedCount(typeof res?.count === 'number' ? res.count : 0);
    } catch {
      setAbortedCount(0);
    }
  }, []);

  useEffect(() => {
    refreshAbortedCount();
  }, [refreshAbortedCount]);

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

  const deleteTrip = useCallback(
    async (tripId) => {
      await deleteTripApi(tripId);

      setDeletedTripIds((prev) => {
        if (prev.has(tripId)) return prev;
        const next = new Set(prev);
        next.add(tripId);
        return next;
      });
      setHistory((prev) => ({
        ...prev,
        items: prev.items.filter((t) => t.id !== tripId),
        count: Math.max(0, prev.count - 1),
        offset: Math.max(0, prev.offset - 1),
      }));
      removeTrip(tripId);
      refreshAbortedCount();
    },
    [removeTrip, refreshAbortedCount]
  );

  const deleteAllAborted = useCallback(async () => {
    const res = await deleteAbortedTrips();
    const deletedCount =
      typeof res?.data?.deleted_count === 'number' ? res.data.deleted_count : 0;

    const seen = new Set();
    const abortedIds = [];
    [...historyRef.current.items, ...(liveTripsRef.current || [])].forEach(
      (t) => {
        if (t && t.status === 'aborted' && t.id && !seen.has(t.id)) {
          seen.add(t.id);
          abortedIds.push(t.id);
        }
      }
    );

    if (deletedCount > 0 || abortedIds.length > 0) {
      setDeletedTripIds((prev) => {
        const next = new Set(prev);
        abortedIds.forEach((id) => next.add(id));
        return next;
      });
      setHistory((prev) => ({
        ...prev,
        items: prev.items.filter((t) => t.status !== 'aborted'),
        count: Math.max(0, prev.count - deletedCount),
        offset: Math.max(0, prev.offset - abortedIds.length),
      }));
      abortedIds.forEach((id) => removeTrip(id));
    }

    refreshAbortedCount();
    return deletedCount;
  }, [removeTrip, refreshAbortedCount]);

  const activeTrips = useMemo(
    () =>
      sortTrips(
        withoutDeleted(liveTrips || []).filter(
          (t) => t.status === 'in_progress' && matchesTripSearch(t, search)
        ),
        sortBy,
        sortAsc
      ),
    [withoutDeleted, liveTrips, search, sortBy, sortAsc]
  );

  const historicalTrips = useMemo(
    () =>
      sortTrips(
        refineTrips(
          withoutDeleted(history.items),
          { search, gradeFilter, dateFrom, dateTo }
        ),
        sortBy,
        sortAsc
      ),
    [withoutDeleted, history.items, search, gradeFilter, dateFrom, dateTo, sortBy, sortAsc]
  );

  const driverOptions = useMemo(() => {
    const seen = new Map();
    [
      ...withoutDeleted(history.items),
      ...withoutDeleted(liveTrips || []),
    ].forEach((t) => {
      if (t.driverId && !seen.has(t.driverId)) {
        seen.set(t.driverId, t.driverName || t.driverId);
      }
    });
    return Array.from(seen, ([value, label]) => ({ value, label }));
  }, [withoutDeleted, history.items, liveTrips]);

  const vehicleOptions = useMemo(() => {
    const seen = new Map();
    [
      ...withoutDeleted(history.items),
      ...withoutDeleted(liveTrips || []),
    ].forEach((t) => {
      if (t.vehicleId && !seen.has(t.vehicleId)) {
        seen.set(t.vehicleId, t.vehicleName || t.vehicleId);
      }
    });
    return Array.from(seen, ([value, label]) => ({ value, label }));
  }, [withoutDeleted, history.items, liveTrips]);

  const summary = useMemo(() => {
    const seen = new Set();
    const all = [];
    [
      ...withoutDeleted(history.items),
      ...withoutDeleted(liveTrips || []),
    ].forEach((t) => {
      if (t && t.id && !seen.has(t.id)) {
        seen.add(t.id);
        all.push(t);
      }
    });
    return computeTripSummary(all);
  }, [withoutDeleted, history.items, liveTrips]);

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
    deleteTrip,
    deleteAllAborted,
    abortedCount,
    summary,
    historyCount: history.count,
    historyLoaded: history.items.length,
    historyError: history.error,
    historyLoading: history.initialLoading,
    historyLoadingMore: history.loadingMore,
    historyHasMore: history.items.length < history.count,
  };
}
