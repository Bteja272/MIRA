import { apiRequest } from "./http";
import type {
  RegistrationResponse,
  TokenResponse,
  User,
} from "../types/auth";

export function registerAccount(
  email: string,
  password: string,
): Promise<RegistrationResponse> {
  return apiRequest<RegistrationResponse>(
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
): Promise<TokenResponse> {
  const form = new URLSearchParams();

  form.set("username", email);
  form.set("password", password);

  return apiRequest<TokenResponse>(
    "/auth/login",
    {
      method: "POST",
      headers: {
        "Content-Type":
          "application/x-www-form-urlencoded",
      },
      body: form,
    },
  );
}

export function getCurrentUser(): Promise<User> {
  return apiRequest<User>("/auth/me");
}