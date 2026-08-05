import {
  createContext,
} from "react";

import type {
  User,
} from "../types/auth";

export type SessionEndReason =
  | "expired"
  | "unauthorized"
  | null;

export interface AuthContextValue {
  user: User | null;
  isInitializing: boolean;
  isAuthenticated: boolean;
  sessionEndReason: SessionEndReason;
  login: (
    email: string,
    password: string,
  ) => Promise<void>;
  register: (
    email: string,
    password: string,
  ) => Promise<void>;
  logout: () => void;
}

export const AuthContext = createContext<
  AuthContextValue | undefined
>(undefined);