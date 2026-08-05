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
  registerAccount,
} from "../api/auth";
import {
  AuthContext,
  type SessionEndReason,
} from "./authContext";
import {
  AUTH_UNAUTHORIZED_EVENT,
  clearAccessToken,
  getAccessToken,
  getTokenExpirationTime,
  isAccessTokenExpired,
  type UnauthorizedReason,
} from "./tokenStorage";
import {
  setAccessToken,
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
  ] = useState<SessionEndReason>(
    null,
  );

  const endSession = useCallback(
    (
      reason: Exclude<
        SessionEndReason,
        null
      > | null,
    ): void => {
      clearAccessToken();
      queryClient.clear();
      setUser(null);
      setSessionEndReason(reason);
    },
    [
      queryClient,
    ],
  );

  const loadCurrentUser = useCallback(
    async (): Promise<void> => {
      const token = getAccessToken();

      if (!token) {
        setUser(null);
        setIsInitializing(false);
        return;
      }

      if (isAccessTokenExpired(token)) {
        endSession("expired");
        setIsInitializing(false);
        return;
      }

      try {
        const currentUser =
          await getCurrentUser();

        setUser(currentUser);
        setSessionEndReason(null);
      } catch {
        endSession("unauthorized");
      } finally {
        setIsInitializing(false);
      }
    },
    [
      endSession,
    ],
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

  useEffect(() => {
    if (!user) {
      return;
    }

    const token = getAccessToken();

    if (!token) {
      endSession("unauthorized");
      return;
    }

    const expirationTime =
      getTokenExpirationTime(token);

    if (expirationTime === null) {
      return;
    }

    const delay = Math.max(
      0,
      expirationTime - Date.now(),
    );

    const timeoutId =
      window.setTimeout(
        () => {
          endSession("expired");
        },
        delay,
      );

    return () => {
      window.clearTimeout(
        timeoutId,
      );
    };
  }, [
    endSession,
    user,
  ]);

  const login = useCallback(
    async (
      email: string,
      password: string,
    ): Promise<void> => {
      const tokenResponse =
        await loginAccount(
          email,
          password,
        );

      queryClient.clear();

      setAccessToken(
        tokenResponse.access_token,
      );

      try {
        const currentUser =
          await getCurrentUser();

        setUser(currentUser);
        setSessionEndReason(null);
      } catch (error) {
        endSession(null);
        throw error;
      }
    },
    [
      endSession,
      queryClient,
    ],
  );

  const register = useCallback(
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
      endSession(null);
    },
    [
      endSession,
    ],
  );

  const value = useMemo(
    () => ({
      user,
      isInitializing,
      isAuthenticated: user !== null,
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
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}