import { ReactNode } from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

interface ProtectedRouteProps {
  children: ReactNode;
  roles?: string[];
}

export const ProtectedRoute = ({ children, roles = [] }: ProtectedRouteProps) => {
  const { user, loading } = useAuth();

  if (loading) {
    return <div className="loading">Проверка авторизации...</div>;
  }

  if (!user) {
    return <Navigate to="/auth" replace />;
  }

  if (roles.length > 0 && !roles.includes(user.role)) {
    return (
      <div className="card" style={{ textAlign: "center", padding: "2rem" }}>
        <p className="error">У вас нет прав для просмотра этой страницы.</p>
        <p className="muted">Требуемые роли: {roles.join(", ")}</p>
      </div>
    );
  }

  return <>{children}</>;
};

