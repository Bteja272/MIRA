import {
  NavLink,
  Outlet,
  useNavigate,
} from "react-router";

import {
  useAuth,
} from "../auth/useAuth";
import {
  MiraBrand,
} from "../components/MiraBrand";


type NavIconName =
  | "overview"
  | "documents"
  | "ask"
  | "extractions"
  | "intelligence";


function NavIcon({
  name,
}: {
  name: NavIconName;
}) {
  if (name === "overview") {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <rect x="3" y="3" width="7" height="7" rx="1.5" />
        <rect x="14" y="3" width="7" height="7" rx="1.5" />
        <rect x="3" y="14" width="7" height="7" rx="1.5" />
        <rect x="14" y="14" width="7" height="7" rx="1.5" />
      </svg>
    );
  }

  if (name === "documents") {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M6 3h8l4 4v14H6z" />
        <path d="M14 3v5h5" />
        <path d="M9 12h6M9 16h6" />
      </svg>
    );
  }

  if (name === "ask") {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M4 5.5A2.5 2.5 0 0 1 6.5 3h11A2.5 2.5 0 0 1 20 5.5v8a2.5 2.5 0 0 1-2.5 2.5H10l-5 4v-4.6A2.5 2.5 0 0 1 4 13.5z" />
      </svg>
    );
  }

  if (name === "extractions") {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M8 5h12M8 12h12M8 19h12" />
        <path d="m3.5 5 1.2 1.2L6.8 4M3.5 12l1.2 1.2L6.8 11M3.5 19l1.2 1.2L6.8 18" />
      </svg>
    );
  }

  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M4 19V9M10 19V5M16 19v-7M22 19H2" />
    </svg>
  );
}


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
  const links: Array<{
    path: string;
    label: string;
    icon: NavIconName;
    end?: boolean;
  }> = [
    {
      path: "/",
      label: "Overview",
      icon: "overview",
      end: true,
    },
    {
      path: "/documents",
      label: "Documents",
      icon: "documents",
    },
    {
      path: "/ask",
      label: "Ask MIRA",
      icon: "ask",
    },
    {
      path: "/extractions",
      label: "Extractions",
      icon: "extractions",
    },
    {
      path: "/intelligence",
      label: "Medical Intelligence",
      icon: "intelligence",
    },
  ];

  return links.map((link) => (
    <NavLink
      key={link.path}
      to={link.path}
      end={link.end}
      className={navClassName}
    >
      <span className="app-nav__icon">
        <NavIcon name={link.icon} />
      </span>
      <span>{link.label}</span>
    </NavLink>
  ));
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

  const initial = (
    user?.email?.trim().charAt(0)
    || "M"
  ).toUpperCase();

  return (
    <div className="app-shell">
      <a
        className="skip-link"
        href="#main-content"
      >
        Skip to main content
      </a>

      <aside className="app-sidebar">
        <div>
          <div className="app-sidebar__brand">
            <MiraBrand inverted />
          </div>

          <nav
            className="app-nav"
            aria-label="Primary"
          >
            {navigationLinks()}
          </nav>
        </div>

        <div className="app-sidebar__footer">
          <div className="privacy-note">
            Synthetic documents only during
            development.
          </div>
        </div>
      </aside>

      <div className="app-main">
        <header className="app-header">
          <div className="app-header__mobile-brand">
            <MiraBrand />
          </div>

          <div className="account-panel">
            <span className="account-email">
              {user?.email}
            </span>

            <button
              className="account-avatar"
              type="button"
              aria-label="Log out"
              title="Log out"
              onClick={handleLogout}
            >
              {initial}
            </button>
          </div>
        </header>

        <nav
          className="app-mobile-nav"
          aria-label="Primary mobile"
        >
          {navigationLinks()}
        </nav>

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
