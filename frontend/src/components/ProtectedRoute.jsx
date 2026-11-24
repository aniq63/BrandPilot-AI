import { Navigate, useLocation } from "react-router-dom";

import { useAuth } from "../auth";

export default function ProtectedRoute({ children }) {
  const { loading, isAuthenticated } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="app-shell">
        <div className="loading-screen">
          <div className="spinner" />
          <p>Loading your workspace…</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  return children;
}
