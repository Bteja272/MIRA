import {
  clearAccessToken,
  getAccessToken,
} from "../auth/tokenStorage";

export const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL
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
    const detail = (body as FastApiErrorBody).detail;

    if (typeof detail === "string") {
      return detail;
    }

    if (Array.isArray(detail)) {
      const messages = detail
        .map((item) => {
          if (
            item
            && typeof item === "object"
            && "msg" in item
            && typeof item.msg === "string"
          ) {
            return item.msg;
          }

          return null;
        })
        .filter(
          (message): message is string => message !== null,
        );

      if (messages.length > 0) {
        return messages.join(" ");
      }
    }

    if (detail && typeof detail === "object") {
      return JSON.stringify(detail);
    }
  }

  if (typeof body === "string" && body.trim()) {
    return body.trim();
  }

  return fallback;
}

export async function apiRequest<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const headers = new Headers(init.headers);
  const token = getAccessToken();

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  if (
    init.body !== undefined
    && !(init.body instanceof FormData)
    && !headers.has("Content-Type")
  ) {
    headers.set("Content-Type", "application/json");
  }

  let response: Response;

  try {
    response = await fetch(
      `${API_BASE_URL}${path}`,
      {
        ...init,
        headers,
      },
    );
  } catch (error) {
    if (
      error instanceof DOMException
      && error.name === "AbortError"
    ) {
      throw error;
    }

    throw new ApiError(
      "The MIRA API could not be reached.",
      0,
      null,
    );
  }

  const contentType = response.headers.get("content-type") ?? "";
  let body: unknown = null;

  if (response.status !== 204) {
    if (contentType.includes("application/json")) {
      body = await response.json();
    } else {
      body = await response.text();
    }
  }

  if (!response.ok) {
    if (response.status === 401) {
      clearAccessToken();
    }

    throw new ApiError(
      extractApiErrorMessage(
        body,
        `Request failed with status ${response.status}.`,
      ),
      response.status,
      body,
    );
  }

  return body as T;
}