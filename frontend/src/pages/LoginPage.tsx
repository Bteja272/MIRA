import {
  useEffect,
  useState,
  type FormEvent,
} from "react";
import {
  Link,
  useLocation,
  useNavigate,
} from "react-router";

import {
  ApiError,
} from "../api/http";
import {
  useAuth,
} from "../auth/useAuth";
import {
  StatusBanner,
} from "../components/StatusBanner";
import type {
  SessionEndReason,
} from "../auth/authContext";

interface LocationState {
  from?: string;
  reason?: SessionEndReason;
}

function safeDestination(
  value: string | undefined,
): string {
  if (
    !value
    || !value.startsWith("/")
    || value.startsWith("//")
  ) {
    return "/";
  }

  return value;
}

function sessionMessage(
  reason: SessionEndReason,
): string | null {
  if (reason === "expired") {
    return (
      "Your session expired. Log in again "
      + "to continue."
    );
  }

  if (reason === "unauthorized") {
    return (
      "Your session is no longer valid. "
      + "Log in again to continue."
    );
  }

  return null;
}

export function LoginPage() {
  const {
    login,
    isAuthenticated,
  } = useAuth();

  const navigate =
    useNavigate();

  const location =
    useLocation();

  const [
    email,
    setEmail,
  ] = useState("");

  const [
    password,
    setPassword,
  ] = useState("");

  const [
    error,
    setError,
  ] = useState<string | null>(
    null,
  );

  const [
    isSubmitting,
    setIsSubmitting,
  ] = useState(false);

  const state =
    location.state as
      | LocationState
      | null;

  const destination =
    safeDestination(
      state?.from,
    );

  const endedSessionMessage =
    sessionMessage(
      state?.reason ?? null,
    );

  useEffect(() => {
    if (isAuthenticated) {
      navigate(
        destination,
        {
          replace: true,
        },
      );
    }
  }, [
    destination,
    isAuthenticated,
    navigate,
  ]);

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ): Promise<void> {
    event.preventDefault();

    setError(null);
    setIsSubmitting(true);

    try {
      await login(
        email.trim().toLowerCase(),
        password,
      );

      navigate(
        destination,
        {
          replace: true,
        },
      );
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught.message
          : "Login failed.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main
      id="main-content"
      className="auth-page"
      tabIndex={-1}
    >
      <section className="auth-panel">
        <div className="auth-copy">
          <p className="eyebrow">
            Medical document intelligence
          </p>

          <h1>Welcome to MIRA</h1>

          <p>
            Review uploaded medical documents,
            ask grounded questions, and inspect
            structured facts with source evidence.
          </p>
        </div>

        <form
          className="auth-form"
          onSubmit={handleSubmit}
          aria-busy={isSubmitting}
        >
          <div>
            <p className="eyebrow">
              Secure account access
            </p>

            <h2>Log in</h2>
          </div>

          {endedSessionMessage && (
            <StatusBanner tone="info">
              {endedSessionMessage}
            </StatusBanner>
          )}

          {error && (
            <StatusBanner tone="error">
              {error}
            </StatusBanner>
          )}

          <label
            className="field"
            htmlFor="login-email"
          >
            <span>Email</span>

            <input
              id="login-email"
              type="email"
              autoComplete="email"
              inputMode="email"
              autoFocus
              required
              disabled={isSubmitting}
              value={email}
              onChange={(event) =>
                setEmail(
                  event.target.value,
                )
              }
            />
          </label>

          <label
            className="field"
            htmlFor="login-password"
          >
            <span>Password</span>

            <input
              id="login-password"
              type="password"
              autoComplete="current-password"
              required
              disabled={isSubmitting}
              value={password}
              onChange={(event) =>
                setPassword(
                  event.target.value,
                )
              }
            />
          </label>

          <button
            className="button button--primary"
            type="submit"
            disabled={isSubmitting}
          >
            {isSubmitting
              ? "Logging in…"
              : "Log in"}
          </button>

          <p className="form-footer">
            Need an account?{" "}
            <Link to="/register">
              Create one
            </Link>
          </p>
        </form>
      </section>
    </main>
  );
}