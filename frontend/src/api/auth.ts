import {
  apiRequest,
} from "./http";

import type {
  AuthSessionResponse,
  LogoutResponse,
  RegistrationResponse,
  User,
} from "../types/auth";

export function registerAccount(
  email: string,
  password: string,
): Promise<RegistrationResponse> {
  return apiRequest<
    RegistrationResponse
  >(
    "/auth/register",
    {
      method: "POST",
      body: JSON.stringify({
        email,
        password,
      }),
    },
  );
}

export function loginAccount(
  email: string,
  password: string,
): Promise<AuthSessionResponse> {
  const form =
    new URLSearchParams();

  form.set(
    "username",
    email,
  );

  form.set(
    "password",
    password,
  );

  return apiRequest<
    AuthSessionResponse
  >(
    "/auth/login",
    {
      method: "POST",
      headers: {
        "Content-Type":
          "application/"
          + "x-www-form-urlencoded",
      },
      body: form,
    },
  );
}

export function refreshSession():
  Promise<AuthSessionResponse> {
  return apiRequest<
    AuthSessionResponse
  >(
    "/auth/refresh",
    {
      method: "POST",
    },
  );
}

export function logoutAccount():
  Promise<LogoutResponse> {
  return apiRequest<
    LogoutResponse
  >(
    "/auth/logout",
    {
      method: "POST",
    },
  );
}

export function getCurrentUser():
  Promise<User> {
  return apiRequest<User>(
    "/auth/me",
  );
}