import { useContext } from "react";
import { FleetContext } from "./fleetCtx";

export function useFleetContext() {
  return useContext(FleetContext);
}
