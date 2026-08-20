import { useState, useEffect, useCallback, useMemo } from 'react';
import {
  getAnalyticsSummary,
  getFleetTrend,
  getDriverRanking,
  getDriverTrend,
  getSafetyDistribution,
  getVehicleAnalytics,
  getTripAnalytics,
  getEventBreakdown,
  getEventTrend,
  getInsights,
} from '../services/api/analyticsApi';

const RANGE_PRESETS = [
  { key: 'last_7_days', label: 'Last 7 days' },
  { key: 'last_30_days', label: 'Last 30 days' },
  { key: 'last_90_days', label: 'Last 90 days' },
  { key: 'last_6_months', label: 'Last 6 months' },
  { key: 'custom', label: 'Custom' },
];

function buildParams(range, customStart, customEnd, vehicleId, driverId) {
  const p = {};
  if (range) p.range = range;
  if (range === 'custom' && customStart) p.custom_start = customStart;
  if (range === 'custom' && customEnd) p.custom_end = customEnd;
  if (vehicleId) p.vehicle_id = vehicleId;
  if (driverId) p.driver_id = driverId;
  return p;
}

export function useAnalytics() {
  const [range, setRange] = useState('last_30_days');
  const [customStart, setCustomStart] = useState('');
  const [customEnd, setCustomEnd] = useState('');
  const [vehicleFilter, setVehicleFilter] = useState('');
  const [driverFilter, setDriverFilter] = useState('');
  const [selectedDriverId, setSelectedDriverId] = useState(null);

  const [summary, setSummary] = useState(null);
  const [fleetTrend, setFleetTrend] = useState(null);
  const [driverRanking, setDriverRanking] = useState(null);
  const [driverTrend, setDriverTrend] = useState(null);
  const [safetyDist, setSafetyDist] = useState(null);
  const [vehicleAnalytics, setVehicleAnalytics] = useState(null);
  const [tripSummary, setTripSummary] = useState(null);
  const [eventBreakdown, setEventBreakdown] = useState(null);
  const [eventTrend, setEventTrend] = useState(null);
  const [insights, setInsights] = useState(null);

  const [loading, setLoading] = useState(true);
  const [errors, setErrors] = useState({});

  const params = useMemo(
    () => buildParams(range, customStart, customEnd, vehicleFilter, driverFilter),
    [range, customStart, customEnd, vehicleFilter, driverFilter]
  );

  const fetchAll = useCallback(async () => {
    setLoading(true);
    setErrors({});

    const results = await Promise.allSettled([
      getAnalyticsSummary(params),
      getFleetTrend(params),
      getDriverRanking(params),
      getSafetyDistribution(),
      getVehicleAnalytics(params),
      getTripAnalytics(params),
      getEventBreakdown(params),
      getEventTrend(params),
      getInsights(params),
    ]);

    const errs = {};
    if (results[0].status === 'fulfilled') setSummary(results[0].value.data);
    else errs.summary = results[0].reason?.message;

    if (results[1].status === 'fulfilled') setFleetTrend(results[1].value.data);
    else errs.fleetTrend = results[1].reason?.message;

    if (results[2].status === 'fulfilled') setDriverRanking(results[2].value.data);
    else errs.driverRanking = results[2].reason?.message;

    if (results[3].status === 'fulfilled') setSafetyDist(results[3].value.data);
    else errs.safetyDist = results[3].reason?.message;

    if (results[4].status === 'fulfilled') setVehicleAnalytics(results[4].value.data);
    else errs.vehicleAnalytics = results[4].reason?.message;

    if (results[5].status === 'fulfilled') setTripSummary(results[5].value.data);
    else errs.tripSummary = results[5].reason?.message;

    if (results[6].status === 'fulfilled') setEventBreakdown(results[6].value.data);
    else errs.eventBreakdown = results[6].reason?.message;

    if (results[7].status === 'fulfilled') setEventTrend(results[7].value.data);
    else errs.eventTrend = results[7].reason?.message;

    if (results[8].status === 'fulfilled') setInsights(results[8].value.data);
    else errs.insights = results[8].reason?.message;

    setErrors(errs);
    setLoading(false);
  }, [params]);

  useEffect(() => {
    const id = setTimeout(() => fetchAll(), 0);
    return () => clearTimeout(id);
  }, [fetchAll]);

  // Fetch driver trend when a driver is selected
  useEffect(() => {
    if (!selectedDriverId) {
      const id = setTimeout(() => setDriverTrend(null), 0);
      return () => clearTimeout(id);
    }
    let cancelled = false;
    getDriverTrend(selectedDriverId, params).then((res) => {
      if (!cancelled) setDriverTrend(res.data);
    }).catch(() => {
      if (!cancelled) setDriverTrend(null);
    });
    return () => { cancelled = true; };
  }, [selectedDriverId, params]);

  return {
    range,
    setRange,
    customStart,
    setCustomStart,
    customEnd,
    setCustomEnd,
    vehicleFilter,
    setVehicleFilter,
    driverFilter,
    setDriverFilter,
    selectedDriverId,
    setSelectedDriverId,
    summary,
    fleetTrend,
    driverRanking,
    driverTrend,
    safetyDist,
    vehicleAnalytics,
    tripSummary,
    eventBreakdown,
    eventTrend,
    insights,
    loading,
    errors,
    refresh: fetchAll,
    presets: RANGE_PRESETS,
  };
}
