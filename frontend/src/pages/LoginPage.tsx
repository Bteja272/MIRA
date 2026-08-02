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

import { ApiError } from "../api/http";
import { useAuth } from "../auth/AuthProvider";
import { StatusBanner } from "../components/StatusBanner";

interface LocationState {
  from?: string;
}

export function LoginPage() {
  const {
    login,
    isAuthenticated,
  } = useAuth();

  const navigate = useNavigate();
  const location = useLocation();

  const [email, setEmail] = useState("");
  const [password, setPassword] =
    useState("");
  const [error, setError] = useState<
    string | null
  >(null);
  const [isSubmitting, setIsSubmitting] =
    useState(false);

  const state = location.state as
    | LocationState
    | null;

  const destination = state?.from ?? "/";

  useEffect(() => {
    if (isAuthenticated) {
      navigate(destination, {
        replace: true,
      });
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

      navigate(destination, {
        replace: true,
      });
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
    <main className="auth-page">
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
        >
          <div>
            <p className="eyebrow">
              Secure account access
            </p>
            <h2>Log in</h2>
          </div>

          {error && (
            <StatusBanner tone="error">
              {error}
            </StatusBanner>
          )}

          <label className="field">
            <span>Email</span>
            <input
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(event) =>
                setEmail(event.target.value)
              }
            />
          </label>

          <label className="field">
            <span>Password</span>
            <input
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(event) =>
                setPassword(event.target.value)
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