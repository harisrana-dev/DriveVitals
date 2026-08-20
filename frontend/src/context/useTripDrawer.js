import { useContext } from "react";
import { TripDrawerContext } from "./tripDrawerCtx";

export function useTripDrawer() {
  const ctx = useContext(TripDrawerContext);
  if (!ctx) {
    throw new Error('useTripDrawer must be used within a TripDrawerProvider');
  }
  return ctx;
}
