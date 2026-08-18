import { useEffect, useMemo, useState } from 'react';
import { listTrips } from '../services/api/tripApi';
import { mapTrips } from '../utils/trips';

const DRIVER_TRIP_LIMIT = 20;

/**
 * Fetches a driver's completed trip history from the trips REST API.
 * Kept separate from the live context so the drawer always reflects the
 * persisted record, independent of WebSocket snapshots.
 *
 * The hook is expected to be remounted per driver (callers use a
 * `key={driverId}`), so `loading` starts truthy for the first fetch.
 */
export function useDriverTrips(driverId) {
  const [trips, setTrips] = useState([]);
  const [loading, setLoading] = useState(() => !!driverId);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    if (!driverId) return;
    let cancelled = false;
    listTrips({ driver_id: driverId, status: 'completed', limit: DRIVER_TRIP_LIMIT })
      .then((res) => {
        if (cancelled) return;
        setTrips(mapTrips(res?.data || []));
      })
      .catch(() => {
        if (!cancelled) setTrips([]);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [driverId, reloadKey]);

  const refresh = useMemo(
    () => () => {
      setLoading(true);
      setReloadKey((k) => k + 1);
    },
    []
  );

  return { trips, loading, refresh };
}
