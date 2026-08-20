import { useContext } from "react";
import { LiveDataContext } from "./liveDataCtx";

export function useLiveData() {
  return useContext(LiveDataContext);
}
