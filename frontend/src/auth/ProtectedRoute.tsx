import {
  Navigate,
  Outlet,
  useLocation,
} from "react-router";

import {
  useAuth,
} from "./useAuth";

export function ProtectedRoute() {
  const {
    isAuthenticated,
    isInitializing,
    sessionEndReason,
  } = useAuth();

  const location = useLocation();

  if (isInitializing) {
    return (
      <main
        id="main-content"
        className="centered-page"
        tabIndex={-1}
      >
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
          from:
            location.pathname
            + location.search,
          reason: sessionEndReason,
        }}
      />
    );
  }

  return <Outlet />;
}