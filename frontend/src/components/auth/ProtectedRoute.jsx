import { Navigate, Outlet } from "react-router-dom";
import AppLoader from "../common/AppLoader";
import { useAuth } from "../../hooks/useAuth";

export function ProtectedRoute() {
  const { status } = useAuth();

  if (status === "loading") {
    return <AppLoader />;
  }
  if (status !== "authenticated") {
    return <Navigate to="/login" replace />;
  }
  return <Outlet />;
}

export default ProtectedRoute;