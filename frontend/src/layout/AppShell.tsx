import {
  NavLink,
  Outlet,
  useNavigate,
} from "react-router";

import {
  useAuth,
} from "../auth/useAuth";


function navClassName({
  isActive,
}: {
  isActive: boolean;
}): string {
  return isActive
    ? (
      "app-nav__link "
      + "app-nav__link--active"
    )
    : "app-nav__link";
}


function navigationLinks() {
  return (
    <>
      <NavLink
        to="/"
        end
        className={navClassName}
      >
        Overview
      </NavLink>

      <NavLink
        to="/documents"
        className={navClassName}
      >
        Documents
      </NavLink>

      <NavLink
        to="/ask"
        className={navClassName}
      >
        Ask MIRA
      </NavLink>

      <NavLink
        to="/extractions"
        className={navClassName}
      >
        Extractions
      </NavLink>

      <NavLink
        to="/intelligence"
        className={navClassName}
      >
        Medical Intelligence
      </NavLink>
    </>
  );
}


export function AppShell() {
  const {
    user,
    logout,
  } = useAuth();

  const navigate =
    useNavigate();

  function handleLogout(): void {
    logout();

    navigate(
      "/login",
      {
        replace: true,
      },
    );
  }

  return (
    <div className="app-shell">
      <a
        className="skip-link"
        href="#main-content"
      >
        Skip to main content
      </a>

      <header className="app-header">
        <div>
          <p className="eyebrow">
            Medical Intelligence & Retrieval
            Assistant
          </p>

          <h1 className="app-title">
            MIRA
          </h1>
        </div>

        <div className="account-panel">
          <span className="account-email">
            {user?.email}
          </span>

          <button
            className="button button--secondary"
            type="button"
            onClick={handleLogout}
          >
            Log out
          </button>
        </div>
      </header>

      <nav
        className="app-mobile-nav"
        aria-label="Primary mobile"
      >
        {navigationLinks()}
      </nav>

      <div className="app-body">
        <aside className="app-sidebar">
          <nav
            className="app-nav"
            aria-label="Primary"
          >
            {navigationLinks()}
          </nav>

          <div className="privacy-note">
            Development environment only. Use
            synthetic documents during frontend
            development.
          </div>
        </aside>

        <main
          id="main-content"
          className="app-content"
          tabIndex={-1}
        >
          <Outlet />
        </main>
      </div>
    </div>
  );
}