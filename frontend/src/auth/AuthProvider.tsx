import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type PropsWithChildren,
} from "react";

import {
  getCurrentUser,
  loginAccount,
  registerAccount,
} from "../api/auth";
import {
  clearAccessToken,
  getAccessToken,
  setAccessToken,
} from "./tokenStorage";
import type { User } from "../types/auth";

interface AuthContextValue {
  user: User | null;
  isInitializing: boolean;
  isAuthenticated: boolean;
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

const AuthContext = createContext<
  AuthContextValue | undefined
>(undefined);

export function AuthProvider({
  children,
}: PropsWithChildren) {
  const [user, setUser] = useState<User | null>(
    null,
  );

  const [
    isInitializing,
    setIsInitializing,
  ] = useState(true);

  const loadCurrentUser = useCallback(
    async (): Promise<void> => {
      const token = getAccessToken();

      if (!token) {
        setUser(null);
        setIsInitializing(false);
        return;
      }

      try {
        const currentUser =
          await getCurrentUser();

        setUser(currentUser);
      } catch {
        clearAccessToken();
        setUser(null);
      } finally {
        setIsInitializing(false);
      }
    },
    [],
  );

  useEffect(() => {
    void loadCurrentUser();
  }, [loadCurrentUser]);

  const login = useCallback(
    async (
      email: string,
      password: string,
    ): Promise<void> => {
      const tokenResponse =
        await loginAccount(email, password);

      setAccessToken(
        tokenResponse.access_token,
      );

      try {
        const currentUser =
          await getCurrentUser();

        setUser(currentUser);
      } catch (error) {
        clearAccessToken();
        setUser(null);
        throw error;
      }
    },
    [],
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
    [login],
  );

  const logout = useCallback((): void => {
    clearAccessToken();
    setUser(null);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isInitializing,
      isAuthenticated: user !== null,
      login,
      register,
      logout,
    }),
    [
      user,
      isInitializing,
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

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error(
      "useAuth must be used inside AuthProvider.",
    );
  }

  return context;
}