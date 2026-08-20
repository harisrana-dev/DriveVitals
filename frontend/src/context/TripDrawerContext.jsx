import { useState, useCallback } from 'react';
import { TripDrawerContext } from "./tripDrawerCtx";

export function TripDrawerProvider({ children }) {
  const [selectedTrip, setSelectedTrip] = useState(null);

  const openDrawer = useCallback((trip) => {
    setSelectedTrip(trip ?? null);
  }, []);

  const closeDrawer = useCallback(() => {
    setSelectedTrip(null);
  }, []);

  return (
    <TripDrawerContext.Provider
      value={{
        selectedTrip,
        openDrawer,
        closeDrawer,
      }}
    >
      {children}
    </TripDrawerContext.Provider>
  );
}
