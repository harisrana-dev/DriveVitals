import { createContext, useContext, useState, useCallback } from 'react';

const TripDrawerContext = createContext(null);

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

export function useTripDrawer() {
  const ctx = useContext(TripDrawerContext);
  if (!ctx) {
    throw new Error('useTripDrawer must be used within a TripDrawerProvider');
  }
  return ctx;
}
