export const TRIP_PAGE_SIZE = 50;

export function statusQueryValue(statusFilter) {
  switch (statusFilter) {
    case 'in_progress':
      return 'in_progress';
    case 'completed':
      return 'completed';
    case 'aborted':
      return 'aborted';
    default:
      return 'completed,aborted';
  }
}

export function buildTripQuery({ statusFilter, routeFilter, driverFilter, vehicleFilter }) {
  const params = { limit: TRIP_PAGE_SIZE };
  params.status = statusQueryValue(statusFilter);
  if (routeFilter) params.route_type = routeFilter;
  if (driverFilter) params.driver_id = driverFilter;
  if (vehicleFilter) params.vehicle_id = vehicleFilter;
  return params;
}

export function matchesTripSearch(trip, query) {
  if (!query || !query.trim()) return true;
  const q = query.toLowerCase();
  return (
    (trip.vehicleName || '').toLowerCase().includes(q) ||
    (trip.vehicleId || '').toLowerCase().includes(q) ||
    (trip.driverName || '').toLowerCase().includes(q) ||
    (trip.driverId || '').toLowerCase().includes(q) ||
    (trip.id || '').toLowerCase().includes(q) ||
    (trip.routeName || '').toLowerCase().includes(q)
  );
}

function tripDateMs(trip) {
  const value = trip.completedAt || trip.startedAt;
  if (!value) return Number.NaN;
  return new Date(value).getTime();
}

export function refineTrips(trips, { search, gradeFilter, dateFrom, dateTo }) {
  let result = Array.isArray(trips) ? trips : [];

  if (search && search.trim()) {
    result = result.filter((t) => matchesTripSearch(t, search));
  }

  if (gradeFilter) {
    result = result.filter((t) => t.grade === gradeFilter);
  }

  if (dateFrom) {
    const from = new Date(`${dateFrom}T00:00:00`).getTime();
    result = result.filter((t) => {
      const ts = tripDateMs(t);
      return !Number.isNaN(ts) && ts >= from;
    });
  }

  if (dateTo) {
    const to = new Date(`${dateTo}T23:59:59.999`).getTime();
    result = result.filter((t) => {
      const ts = tripDateMs(t);
      return !Number.isNaN(ts) && ts <= to;
    });
  }

  return result;
}

function compareNullableNumeric(a, b, sortAsc) {
  const aNull = a == null;
  const bNull = b == null;
  if (aNull && bNull) return 0;
  if (aNull) return 1;
  if (bNull) return -1;
  const cmp = a - b;
  return sortAsc ? cmp : -cmp;
}

function compareNullableString(a, b, sortAsc) {
  const aNull = a == null || a === '';
  const bNull = b == null || b === '';
  if (aNull && bNull) return 0;
  if (aNull) return 1;
  if (bNull) return -1;
  const cmp = String(a).localeCompare(String(b));
  return sortAsc ? cmp : -cmp;
}

export function sortTrips(trips, sortBy, sortAsc) {
  const result = [...(Array.isArray(trips) ? trips : [])];
  result.sort((a, b) => {
    let cmp;
    switch (sortBy) {
      case 'distance':
        cmp = compareNullableNumeric(a.distance, b.distance, sortAsc);
        break;
      case 'duration':
        cmp = compareNullableNumeric(a.duration, b.duration, sortAsc);
        break;
      case 'score':
        cmp = compareNullableNumeric(a.safetyScore, b.safetyScore, sortAsc);
        break;
      case 'fuel':
        cmp = compareNullableNumeric(a.fuelConsumed, b.fuelConsumed, sortAsc);
        break;
      case 'date':
      default:
        cmp = compareNullableString(
          a.completedAt || a.startedAt || '',
          b.completedAt || b.startedAt || '',
          sortAsc
        );
        break;
    }
    return cmp;
  });
  return result;
}

export function computeTripSummary(trips) {
  const list = Array.isArray(trips) ? trips : [];

  let totalDistance = 0;
  let totalFuel = 0;
  const scores = [];

  for (const t of list) {
    if (t.distance != null) totalDistance += t.distance;
    if (t.fuelConsumed != null) totalFuel += t.fuelConsumed;
    if (t.safetyScore != null) scores.push(t.safetyScore);
  }

  return {
    totalTrips: list.length,
    totalDistance,
    totalFuel,
    avgSafetyScore: scores.length > 0
      ? scores.reduce((sum, s) => sum + s, 0) / scores.length
      : 0,
  };
}
