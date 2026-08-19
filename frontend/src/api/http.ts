import {
  getCsrfToken,
  notifyUnauthorized,
} from "../auth/tokenStorage";

export const API_BASE_URL = (
  import.meta.env
    .VITE_API_BASE_URL
  ?? "http://127.0.0.1:8001"
).replace(/\/+$/, "");

type FastApiErrorBody = {
  detail?: unknown;
};

export class ApiError extends Error {
  readonly status: number;
  readonly body: unknown;

  constructor(
    message: string,
    status: number,
    body: unknown,
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }
}

export function extractApiErrorMessage(
  body: unknown,
  fallback: string,
): string {
  if (
    body
    && typeof body === "object"
    && "detail" in body
  ) {
    const detail =
      (body as FastApiErrorBody)
        .detail;

    if (
      typeof detail
      === "string"
    ) {
      return detail;
    }

    if (Array.isArray(detail)) {
      const messages = detail
        .map((item) => {
          if (
            item
            && typeof item
              === "object"
            && "msg" in item
            && typeof item.msg
              === "string"
          ) {
            return item.msg;
          }

          return null;
        })
        .filter(
          (
            message,
          ): message is string =>
            message !== null,
        );

      if (
        messages.length > 0
      ) {
        return messages.join(
          " ",
        );
      }
    }

    if (
      detail
      && typeof detail
        === "object"
    ) {
      return JSON.stringify(
        detail,
      );
    }
  }

  if (
    typeof body === "string"
    && body.trim()
  ) {
    return body.trim();
  }

  return fallback;
}

async function parseResponseBody(
  response: Response,
): Promise<unknown> {
  if (response.status === 204) {
    return null;
  }

  const rawBody =
    await response.text();

  if (!rawBody) {
    return null;
  }

  const contentType =
    response.headers.get(
      "content-type",
    ) ?? "";

  if (
    contentType.includes(
      "application/json",
    )
  ) {
    try {
      return JSON.parse(
        rawBody,
      ) as unknown;
    } catch {
      return rawBody;
    }
  }

  return rawBody;
}

const UNSAFE_METHODS =
  new Set([
    "POST",
    "PUT",
    "PATCH",
    "DELETE",
  ]);

let refreshPromise:
  Promise<boolean> | null =
    null;

function buildHeaders(
  init: RequestInit,
): Headers {
  const headers =
    new Headers(init.headers);

  headers.set(
    "Accept",
    "application/json",
  );

  if (
    init.body !== undefined
    && !(
      init.body
      instanceof FormData
    )
    && !headers.has(
      "Content-Type",
    )
  ) {
    headers.set(
      "Content-Type",
      "application/json",
    );
  }

  const method = (
    init.method ?? "GET"
  ).toUpperCase();

  if (
    UNSAFE_METHODS.has(
      method,
    )
  ) {
    const csrfToken =
      getCsrfToken();

    if (csrfToken) {
      headers.set(
        "X-CSRF-Token",
        csrfToken,
      );
    }
  }

  return headers;
}

async function performRefresh():
  Promise<boolean> {
  if (refreshPromise) {
    return refreshPromise;
  }

  refreshPromise = (
    async () => {
      const headers =
        new Headers();

      headers.set(
        "Accept",
        "application/json",
      );

      const csrfToken =
        getCsrfToken();

      if (csrfToken) {
        headers.set(
          "X-CSRF-Token",
          csrfToken,
        );
      }

      try {
        const response =
          await fetch(
            (
              `${API_BASE_URL}`
              + "/auth/refresh"
            ),
            {
              method: "POST",
              headers,
              credentials:
                "include",
            },
          );

        return response.ok;
      } catch {
        return false;
      }
    }
  )();

  try {
    return await refreshPromise;
  } finally {
    refreshPromise = null;
  }
}

function canAttemptRefresh(
  path: string,
): boolean {
  return ![
    "/auth/login",
    "/auth/register",
    "/auth/refresh",
  ].includes(path);
}

export async function apiRequest<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  async function execute(
    allowRefresh: boolean,
  ): Promise<T> {
    const headers =
      buildHeaders(init);

    let response: Response;

    try {
      response = await fetch(
        `${API_BASE_URL}${path}`,
        {
          ...init,
          headers,
          credentials: "include",
        },
      );
    } catch (error) {
      if (
        error
        instanceof DOMException
        && error.name
          === "AbortError"
      ) {
        throw error;
      }

      throw new ApiError(
        (
          "The MIRA API "
          + "could not be reached."
        ),
        0,
        null,
      );
    }

    if (
      response.status === 401
      && allowRefresh
      && canAttemptRefresh(
        path,
      )
    ) {
      const refreshed =
        await performRefresh();

      if (refreshed) {
        // Rebuild headers on the
        // retry so the newly rotated
        // CSRF cookie is used.
        return execute(false);
      }

      notifyUnauthorized(
        "expired",
      );
    }

    const body =
      await parseResponseBody(
        response,
      );

    if (!response.ok) {
      if (
        response.status === 401
      ) {
        notifyUnauthorized(
          "unauthorized",
        );
      }

      throw new ApiError(
        extractApiErrorMessage(
          body,
          (
            "Request failed "
            + "with status "
            + response.status
            + "."
          ),
        ),
        response.status,
        body,
      );
    }

    return body as T;
  }

  return execute(true);
}