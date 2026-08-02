import {
  useEffect,
  useState,
  type FormEvent,
} from "react";
import {
  Link,
  useNavigate,
} from "react-router";

import { ApiError } from "../api/http";
import { useAuth } from "../auth/AuthProvider";
import { StatusBanner } from "../components/StatusBanner";

export function RegisterPage() {
  const {
    register,
    isAuthenticated,
  } = useAuth();

  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] =
    useState("");
  const [
    confirmPassword,
    setConfirmPassword,
  ] = useState("");
  const [error, setError] = useState<
    string | null
  >(null);
  const [isSubmitting, setIsSubmitting] =
    useState(false);

  useEffect(() => {
    if (isAuthenticated) {
      navigate("/", {
        replace: true,
      });
    }
  }, [
    isAuthenticated,
    navigate,
  ]);

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ): Promise<void> {
    event.preventDefault();

    setError(null);

    if (password !== confirmPassword) {
      setError(
        "The passwords do not match.",
      );
      return;
    }

    setIsSubmitting(true);

    try {
      await register(
        email.trim().toLowerCase(),
        password,
      );

      navigate("/", {
        replace: true,
      });
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught.message
          : "Registration failed.",
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
            Private by account
          </p>
          <h1>Create a MIRA account</h1>
          <p>
            Your uploaded documents, questions,
            and structured extractions are scoped
            to your authenticated account.
          </p>
        </div>

        <form
          className="auth-form"
          onSubmit={handleSubmit}
        >
          <div>
            <p className="eyebrow">
              Development access
            </p>
            <h2>Register</h2>
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
              autoComplete="new-password"
              minLength={12}
              required
              value={password}
              onChange={(event) =>
                setPassword(event.target.value)
              }
            />
            <small>
              Use at least 12 characters.
            </small>
          </label>

          <label className="field">
            <span>Confirm password</span>
            <input
              type="password"
              autoComplete="new-password"
              minLength={12}
              required
              value={confirmPassword}
              onChange={(event) =>
                setConfirmPassword(
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
              ? "Creating account…"
              : "Create account"}
          </button>

          <p className="form-footer">
            Already registered?{" "}
            <Link to="/login">
              Log in
            </Link>
          </p>
        </form>
      </section>
    </main>
  );
}