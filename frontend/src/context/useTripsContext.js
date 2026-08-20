import { useContext } from "react";
import { TripsContext } from "./tripsCtx";

export function useTripsContext() {
  return useContext(TripsContext);
}
