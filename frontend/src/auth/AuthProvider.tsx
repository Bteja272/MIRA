import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  type PropsWithChildren,
} from "react";

import {
  useQueryClient,
} from "@tanstack/react-query";

import {
  getCurrentUser,
  loginAccount,
  logoutAccount,
  registerAccount,
} from "../api/auth";

import {
  AuthContext,
  type SessionEndReason,
} from "./authContext";

import {
  AUTH_UNAUTHORIZED_EVENT,
  type UnauthorizedReason,
} from "./tokenStorage";

import type {
  User,
} from "../types/auth";


export function AuthProvider({
  children,
}: PropsWithChildren) {
  const queryClient =
    useQueryClient();

  const [
    user,
    setUser,
  ] = useState<User | null>(
    null,
  );

  const [
    isInitializing,
    setIsInitializing,
  ] = useState(true);

  const [
    sessionEndReason,
    setSessionEndReason,
  ] = useState<
    SessionEndReason
  >(null);

  const endSession =
    useCallback(
      (
        reason: Exclude<
          SessionEndReason,
          null
        > | null,
      ): void => {
        queryClient.clear();

        setUser(null);

        setSessionEndReason(
          reason,
        );
      },
      [
        queryClient,
      ],
    );

  const loadCurrentUser =
    useCallback(
      async (): Promise<void> => {
        try {
          const currentUser =
            await getCurrentUser();

          setUser(
            currentUser,
          );

          setSessionEndReason(
            null,
          );
        } catch {
          setUser(null);
        } finally {
          setIsInitializing(
            false,
          );
        }
      },
      [],
    );

  useEffect(() => {
    void loadCurrentUser();
  }, [
    loadCurrentUser,
  ]);

  useEffect(() => {
    function handleUnauthorized(
      event: Event,
    ): void {
      const customEvent =
        event as CustomEvent<
          UnauthorizedReason
        >;

      endSession(
        customEvent.detail
        ?? "unauthorized",
      );
    }

    window.addEventListener(
      AUTH_UNAUTHORIZED_EVENT,
      handleUnauthorized,
    );

    return () => {
      window.removeEventListener(
        AUTH_UNAUTHORIZED_EVENT,
        handleUnauthorized,
      );
    };
  }, [
    endSession,
  ]);

  const login = useCallback(
    async (
      email: string,
      password: string,
    ): Promise<void> => {
      const session =
        await loginAccount(
          email,
          password,
        );

      queryClient.clear();

      setUser(
        session.user,
      );

      setSessionEndReason(
        null,
      );
    },
    [
      queryClient,
    ],
  );

  const register =
    useCallback(
      async (
        email: string,
        password: string,
      ): Promise<void> => {
        await registerAccount(
          email,
          password,
        );

        await login(
          email,
          password,
        );
      },
      [
        login,
      ],
    );

  const logout = useCallback(
    (): void => {
      void (
        async () => {
          try {
            await logoutAccount();
          } finally {
            endSession(null);
          }
        }
      )();
    },
    [
      endSession,
    ],
  );

  const value = useMemo(
    () => ({
      user,
      isInitializing,
      isAuthenticated:
        user !== null,
      sessionEndReason,
      login,
      register,
      logout,
    }),
    [
      user,
      isInitializing,
      sessionEndReason,
      login,
      register,
      logout,
    ],
  );

  return (
    <AuthContext.Provider
      value={value}
    >
      {children}
    </AuthContext.Provider>
  );
}