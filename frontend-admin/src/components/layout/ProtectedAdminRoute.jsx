import { Navigate } from "react-router-dom";
import { useAdminAuthStore } from "../../store/adminAuthStore";
import { isAdminRole } from "../../utils/permissions";

export function ProtectedAdminRoute({ children }) {
  const { isAuthenticated, role } = useAdminAuthStore();
  if (!isAuthenticated) return <Navigate to="/admin/login" replace />;
  if (!isAdminRole(role)) return <Navigate to="/admin/login" replace />;
  return children;
}

