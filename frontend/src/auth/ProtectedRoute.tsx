import {
  Navigate,
  Outlet,
  useLocation,
} from "react-router";

import { useAuth } from "./AuthProvider";

export function ProtectedRoute() {
  const {
    isAuthenticated,
    isInitializing,
  } = useAuth();

  const location = useLocation();

  if (isInitializing) {
    return (
      <main className="centered-page">
        <div
          className="loading-card"
          role="status"
          aria-live="polite"
        >
          Checking your session…
        </div>
      </main>
    );
  }

  if (!isAuthenticated) {
    return (
      <Navigate
        to="/login"
        replace
        state={{
          from: location.pathname,
        }}
      />
    );
  }

  return <Outlet />;
}