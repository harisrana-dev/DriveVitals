import { useContext } from "react";
import { AuthContext } from "../context/authCtx";

export function useAuth() {
  return useContext(AuthContext);
}