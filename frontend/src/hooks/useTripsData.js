import { useMemo } from 'react';
import { useTripsContext } from '../context/useTripsContext';
import { mapTrips } from '../utils/trips';

export function useTrips() {
  const { tripsData } = useTripsContext();
  return useMemo(() => mapTrips(tripsData?.trips), [tripsData]);
}

export function useTrip(id) {
  const trips = useTrips();
  return useMemo(() => trips.find((t) => t.id === id), [trips, id]);
}
