const ACCESS_TOKEN_KEY =
  "mira_access_token";

export const AUTH_UNAUTHORIZED_EVENT =
  "mira:unauthorized";

export type UnauthorizedReason =
  | "expired"
  | "unauthorized";

interface JwtPayload {
  exp?: unknown;
}

function decodeBase64Url(
  value: string,
): string {
  const normalized = value
    .replace(/-/g, "+")
    .replace(/_/g, "/");

  const paddingLength =
    (4 - normalized.length % 4) % 4;

  return atob(
    normalized
    + "=".repeat(paddingLength),
  );
}

export function getAccessToken():
  string | null {
  return sessionStorage.getItem(
    ACCESS_TOKEN_KEY,
  );
}

export function setAccessToken(
  token: string,
): void {
  sessionStorage.setItem(
    ACCESS_TOKEN_KEY,
    token,
  );
}

export function clearAccessToken(): void {
  sessionStorage.removeItem(
    ACCESS_TOKEN_KEY,
  );
}

export function getTokenExpirationTime(
  token: string,
): number | null {
  const parts = token.split(".");

  if (parts.length !== 3) {
    return null;
  }

  try {
    const payload = JSON.parse(
      decodeBase64Url(parts[1]),
    ) as JwtPayload;

    if (
      typeof payload.exp !== "number"
      || !Number.isFinite(payload.exp)
    ) {
      return null;
    }

    return payload.exp * 1000;
  } catch {
    return null;
  }
}

export function isAccessTokenExpired(
  token: string,
  clockSkewSeconds = 15,
): boolean {
  const expirationTime =
    getTokenExpirationTime(token);

  if (expirationTime === null) {
    return false;
  }

  return (
    expirationTime
    <= Date.now()
      + clockSkewSeconds * 1000
  );
}

export function notifyUnauthorized(
  reason: UnauthorizedReason,
): void {
  window.dispatchEvent(
    new CustomEvent<UnauthorizedReason>(
      AUTH_UNAUTHORIZED_EVENT,
      {
        detail: reason,
      },
    ),
  );
}