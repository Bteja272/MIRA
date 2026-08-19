export const AUTH_UNAUTHORIZED_EVENT =
  "mira:unauthorized";

export type UnauthorizedReason =
  | "expired"
  | "unauthorized";

const CSRF_COOKIE_NAME =
  import.meta.env
    .VITE_CSRF_COOKIE_NAME
  ?? "mira_csrf";

export function getCsrfToken():
  string | null {
  const prefix =
    `${CSRF_COOKIE_NAME}=`;

  const cookies =
    document.cookie.split(";");

  for (const cookie of cookies) {
    const cleaned =
      cookie.trim();

    if (
      cleaned.startsWith(
        prefix,
      )
    ) {
      return decodeURIComponent(
        cleaned.slice(
          prefix.length,
        ),
      );
    }
  }

  return null;
}

export function notifyUnauthorized(
  reason: UnauthorizedReason,
): void {
  window.dispatchEvent(
    new CustomEvent<
      UnauthorizedReason
    >(
      AUTH_UNAUTHORIZED_EVENT,
      {
        detail: reason,
      },
    ),
  );
}