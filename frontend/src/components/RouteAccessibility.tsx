import {
  useEffect,
} from "react";
import {
  Outlet,
  useLocation,
} from "react-router";

function pageTitle(
  pathname: string,
): string {
  if (
    pathname.startsWith(
      "/documents",
    )
  ) {
    return "Documents | MIRA";
  }

  if (
    pathname.startsWith(
      "/ask",
    )
  ) {
    return "Ask MIRA | MIRA";
  }

  if (
    pathname.startsWith(
      "/extractions",
    )
  ) {
    return "Extractions | MIRA";
  }

  if (
    pathname.startsWith(
      "/login",
    )
  ) {
    return "Log in | MIRA";
  }

  if (
    pathname.startsWith(
      "/register",
    )
  ) {
    return "Register | MIRA";
  }

  if (pathname === "/") {
    return "Overview | MIRA";
  }

  return "Page not found | MIRA";
}

export function RouteAccessibility() {
  const location =
    useLocation();

  useEffect(() => {
    document.title = pageTitle(
      location.pathname,
    );

    const animationFrame =
      window.requestAnimationFrame(
        () => {
          const mainContent =
            document.getElementById(
              "main-content",
            );

          mainContent?.focus();
        },
      );

    return () => {
      window.cancelAnimationFrame(
        animationFrame,
      );
    };
  }, [
    location.pathname,
  ]);

  return <Outlet />;
}