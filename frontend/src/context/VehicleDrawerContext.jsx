import { createContext, useContext, useState, useCallback } from 'react';

const VehicleDrawerContext = createContext(null);

export function VehicleDrawerProvider({ children }) {
  const [selectedVehicleId, setSelectedVehicleId] = useState(null);

  const openDrawer = useCallback((vehicle) => {
    setSelectedVehicleId(vehicle?.id ?? null);
  }, []);

  const closeDrawer = useCallback(() => {
    setSelectedVehicleId(null);
  }, []);

  return (
    <VehicleDrawerContext.Provider
      value={{
        selectedVehicleId,
        openDrawer,
        closeDrawer,
      }}
    >
      {children}
    </VehicleDrawerContext.Provider>
  );
}

export function useVehicleDrawer() {
  const ctx = useContext(VehicleDrawerContext);
  if (!ctx) {
    throw new Error('useVehicleDrawer must be used within a VehicleDrawerProvider');
  }
  return ctx;
}
