import { createContext, useContext, useState, useCallback } from 'react';

const VehicleDrawerContext = createContext(null);

export function VehicleDrawerProvider({ children }) {
  const [selectedVehicleId, setSelectedVehicleId] = useState(null);
  const [drawerDepth, setDrawerDepth] = useState(0);
  const [maintenanceVehicleId, setMaintenanceVehicleId] = useState(null);
  const [maintenanceDepth, setMaintenanceDepth] = useState(0);

  const openDrawer = useCallback((vehicle, depth = 0) => {
    setSelectedVehicleId(vehicle?.id ?? null);
    setDrawerDepth(depth);
  }, []);

  const closeDrawer = useCallback(() => {
    setSelectedVehicleId(null);
    setDrawerDepth(0);
  }, []);

  const openMaintenance = useCallback((vehicleId, depth = 1) => {
    setMaintenanceVehicleId(vehicleId);
    setMaintenanceDepth(depth);
  }, []);

  const closeMaintenance = useCallback(() => {
    setMaintenanceVehicleId(null);
    setMaintenanceDepth(0);
  }, []);

  return (
    <VehicleDrawerContext.Provider
      value={{
        selectedVehicleId,
        drawerDepth,
        openDrawer,
        closeDrawer,
        maintenanceVehicleId,
        maintenanceDepth,
        openMaintenance,
        closeMaintenance,
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
