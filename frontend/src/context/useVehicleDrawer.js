import { useContext } from "react";
import { VehicleDrawerContext } from "./vehicleDrawerCtx";

export function useVehicleDrawer() {
  const ctx = useContext(VehicleDrawerContext);
  if (!ctx) {
    throw new Error('useVehicleDrawer must be used within a VehicleDrawerProvider');
  }
  return ctx;
}
