import {
  useEffect,
  useState,
  type FormEvent,
} from "react";
import {
  Link,
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
import {
  MiraBrand,
} from "../components/MiraBrand";

export function RegisterPage() {
  const {
    register,
    isAuthenticated,
  } = useAuth();

  const navigate =
    useNavigate();

  const [
    email,
    setEmail,
  ] = useState("");

  const [
    password,
    setPassword,
  ] = useState("");

  const [
    confirmPassword,
    setConfirmPassword,
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

  useEffect(() => {
    if (isAuthenticated) {
      navigate(
        "/",
        {
          replace: true,
        },
      );
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

      navigate(
        "/",
        {
          replace: true,
        },
      );
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
    <main
      id="main-content"
      className="auth-page"
      tabIndex={-1}
    >
      <section className="auth-panel auth-panel--calm">
        <div className="auth-brand-panel">
          <MiraBrand inverted />

          <div className="auth-brand-panel__copy">
            <p className="eyebrow">Private by account</p>
            <h1>Create a focused workspace for your medical documents.</h1>
            <p>
              Documents, conversations, and extracted facts
              remain scoped to your authenticated account.
            </p>
          </div>
        </div>

        <form
          className="auth-form"
          onSubmit={handleSubmit}
          aria-busy={isSubmitting}
        >
          <div className="auth-form__heading">
            <p className="eyebrow">Get started</p>
            <h2>Create your account</h2>
            <p>Use synthetic medical records during development.</p>
          </div>

          {error && (
            <StatusBanner tone="error">
              {error}
            </StatusBanner>
          )}

          <label className="field" htmlFor="register-email">
            <span>Email</span>
            <input
              id="register-email"
              type="email"
              autoComplete="email"
              inputMode="email"
              autoFocus
              required
              disabled={isSubmitting}
              value={email}
              placeholder="you@example.com"
              onChange={(event) => setEmail(event.target.value)}
            />
          </label>

          <label className="field" htmlFor="register-password">
            <span>Password</span>
            <input
              id="register-password"
              type="password"
              autoComplete="new-password"
              minLength={12}
              required
              disabled={isSubmitting}
              aria-describedby="register-password-help"
              value={password}
              placeholder="At least 12 characters"
              onChange={(event) => setPassword(event.target.value)}
            />
            <small id="register-password-help">
              Use at least 12 characters.
            </small>
          </label>

          <label className="field" htmlFor="confirm-password">
            <span>Confirm password</span>
            <input
              id="confirm-password"
              type="password"
              autoComplete="new-password"
              minLength={12}
              required
              disabled={isSubmitting}
              value={confirmPassword}
              placeholder="Repeat your password"
              onChange={(event) => setConfirmPassword(event.target.value)}
            />
          </label>

          <button
            className="button button--primary auth-submit"
            type="submit"
            disabled={isSubmitting}
          >
            {isSubmitting ? "Creating account…" : "Create account"}
          </button>

          <p className="form-footer">
            Already registered?{" "}
            <Link to="/login">Log in</Link>
          </p>
        </form>
      </section>
    </main>
  );
}