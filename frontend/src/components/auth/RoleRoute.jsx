import { Navigate, Outlet } from "react-router-dom";
import AppLoader from "../common/AppLoader";
import { useAuth } from "../../hooks/useAuth";
import { Unauthorized } from "../../pages/Unauthorized";

export function RoleRoute({ roles }) {
  const { status, user } = useAuth();

  if (status === "loading") {
    return <AppLoader />;
  }
  if (status !== "authenticated") {
    return <Navigate to="/login" replace />;
  }
  if (!roles.includes(user?.role)) {
    return <Unauthorized />;
  }
  return <Outlet />;
}

export default RoleRoute;