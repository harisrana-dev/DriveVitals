export const TRIP_STATUS_META = {
  in_progress: {
    label: 'In Progress',
    color: 'var(--color-green)',
    bg: 'var(--color-green-bg)',
    pulse: true,
  },
  completed: {
    label: 'Completed',
    color: 'var(--color-accent)',
    bg: 'var(--color-accent-subtle)',
    pulse: false,
  },
  aborted: {
    label: 'Aborted',
    color: 'var(--color-amber)',
    bg: 'var(--color-amber-bg)',
    pulse: false,
  },
  assigned: {
    label: 'Assigned',
    color: 'var(--color-text-muted)',
    bg: 'var(--color-surface-hover)',
    pulse: false,
  },
  started: {
    label: 'Started',
    color: 'var(--color-accent)',
    bg: 'var(--color-accent-subtle)',
    pulse: false,
  },
};

export function tripStatusMeta(status) {
  return TRIP_STATUS_META[status] || null;
}

export function tripIsHistorical(trip) {
  return trip?.status === 'completed' || trip?.status === 'aborted';
}

function gradeColor(grade) {
  if (!grade) return 'var(--color-text-muted)';
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

export function formatDuration(seconds) {
  if (seconds == null || seconds <= 0) return '—';
  const hrs = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  if (hrs > 0) return `${hrs}h ${mins}m`;
  if (mins > 0) return `${mins}m ${secs}s`;
  return `${secs}s`;
}

export function formatDistance(km) {
  if (km == null || km <= 0) return '—';
  if (km < 1) return `${Math.round(km * 1000)} m`;
  return `${km.toFixed(1)} km`;
}

export function formatFuel(liters) {
  if (liters == null || liters <= 0) return '—';
  return `${liters.toFixed(1)} L`;
}

export function mapTrip(t) {
  if (!t) return null;

  return {
    id: t.trip_id,
    vehicleId: t.vehicle_id,
    driverId: t.driver_id,
    vehicleName: t.vehicle_name || t.vehicle_id,
    driverName: t.driver_name || t.driver_id || '—',
    routeId: t.route_id,
    routeType: t.route_type || '—',
    routeName: t.route_name || null,
    distance: t.distance_km ?? null,
    distanceFormatted: formatDistance(t.distance_km),
    duration: t.duration_seconds ?? null,
    durationFormatted: formatDuration(t.duration_seconds),
    averageSpeed: t.average_speed_kmh ?? null,
    maximumSpeed: t.maximum_speed_kmh ?? null,
    fuelConsumed: t.fuel_consumed_liters ?? null,
    fuelFormatted: formatFuel(t.fuel_consumed_liters),
    avgFuelRate: t.average_fuel_rate_lph ?? null,
    safetyScore: t.safety_score ?? null,
    grade: t.grade || null,
    gradeColor: gradeColor(t.grade),
    startedAt: t.started_at || null,
    completedAt: t.completed_at || null,
    status: t.status || null,
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
  };
}

export function mapTrips(raw) {
  if (!raw || !Array.isArray(raw)) return [];
  return raw.map(mapTrip).filter(Boolean);
}
