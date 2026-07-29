import { useMemo } from 'react';
import { useTripsContext } from '../context/TripsContext';

function gradeColor(grade) {
  if (grade === 'A') return 'var(--color-green)';
  if (grade === 'B') return 'var(--color-accent)';
  if (grade === 'C') return 'var(--color-amber)';
  if (grade === 'D') return 'var(--color-amber)';
  return 'var(--color-red)';
}

function severityColor(severity) {
  if (severity === 'severe') return 'var(--color-red)';
  if (severity === 'moderate') return 'var(--color-amber)';
  return 'var(--color-text-muted)';
}

function formatDuration(seconds) {
  if (!seconds || seconds <= 0) return '—';
  const hrs = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  if (hrs > 0) return `${hrs}h ${mins}m`;
  if (mins > 0) return `${mins}m ${secs}s`;
  return `${secs}s`;
}

function formatDistance(km) {
  if (km == null) return '—';
  if (km < 1) return `${Math.round(km * 1000)} m`;
  return `${km.toFixed(1)} km`;
}

function formatFuel(liters) {
  if (liters == null || liters <= 0) return '—';
  return `${liters.toFixed(1)} L`;
}

function mapTrips(raw) {
  if (!raw || !Array.isArray(raw)) return [];
  return raw.map((t) => ({
    id: t.trip_id,
    vehicleId: t.vehicle_id,
    driverId: t.driver_id,
    vehicleName: t.vehicle_name || t.vehicle_id,
    driverName: t.driver_name || t.driver_id || '—',
    routeId: t.route_id,
    routeType: t.route_type || '—',
    distance: t.distance_km ?? 0,
    distanceFormatted: formatDistance(t.distance_km),
    duration: t.duration_seconds ?? 0,
    durationFormatted: formatDuration(t.duration_seconds),
    averageSpeed: t.average_speed_kmh ?? 0,
    maximumSpeed: t.maximum_speed_kmh ?? 0,
    fuelConsumed: t.fuel_consumed_liters ?? 0,
    fuelFormatted: formatFuel(t.fuel_consumed_liters),
    avgFuelRate: t.average_fuel_rate_lph ?? 0,
    safetyScore: t.safety_score ?? 0,
    grade: t.overall_grade || '—',
    gradeColor: gradeColor(t.overall_grade),
    startedAt: t.started_at || null,
    completedAt: t.completed_at || null,
    speedingCount: t.speeding_event_count ?? 0,
    speedingDuration: t.speeding_duration_seconds ?? 0,
    harshBrakingCount: t.harsh_braking_count ?? 0,
    aggressiveThrottleCount: t.aggressive_throttle_event_count ?? 0,
    aggressiveThrottleDuration: t.aggressive_throttle_duration_seconds ?? 0,
    highRpmCount: t.high_rpm_event_count ?? 0,
    highRpmDuration: t.high_rpm_duration_seconds ?? 0,
    severeCount: t.severe_event_count ?? 0,
    moderateCount: t.moderate_event_count ?? 0,
    minorCount: t.minor_event_count ?? 0,
    overallSeverity: t.overall_severity || 'none',
    severityColor: severityColor(t.overall_severity),
    events: t.events || [],
  }));
}

export function useTrips() {
  const { tripsData } = useTripsContext();
  return useMemo(() => mapTrips(tripsData?.trips), [tripsData]);
}

export function useTrip(id) {
  const trips = useTrips();
  return useMemo(() => trips.find((t) => t.id === id), [trips, id]);
}

export function useTripsSummary() {
  const { tripsData } = useTripsContext();

  if (!tripsData) {
    return {
      totalTrips: 0,
      totalDistance: 0,
      avgSafetyScore: 0,
      totalFuel: 0,
    };
  }

  return {
    totalTrips: tripsData.total_trips ?? 0,
    totalDistance: tripsData.total_distance_km ?? 0,
    avgSafetyScore: tripsData.average_safety_score ?? 0,
    totalFuel: tripsData.total_fuel_consumed_liters ?? 0,
  };
}
