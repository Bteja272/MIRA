import {
  Component,
  type ErrorInfo,
  type ReactNode,
} from "react";

interface AppErrorBoundaryProps {
  children: ReactNode;
}

interface AppErrorBoundaryState {
  error: Error | null;
}

export class AppErrorBoundary extends Component<
  AppErrorBoundaryProps,
  AppErrorBoundaryState
> {
  state: AppErrorBoundaryState = {
    error: null,
  };

  static getDerivedStateFromError(
    error: Error,
  ): AppErrorBoundaryState {
    return {
      error,
    };
  }

  componentDidCatch(
    error: Error,
    info: ErrorInfo,
  ): void {
    console.error(
      "MIRA frontend render failure",
      error,
      info,
    );
  }

  private reloadApplication = (): void => {
    window.location.reload();
  };

  render(): ReactNode {
    const {
      error,
    } = this.state;

    if (!error) {
      return this.props.children;
    }

    return (
      <main
        id="main-content"
        className="centered-page"
        tabIndex={-1}
      >
        <section
          className="error-boundary-card"
          role="alert"
        >
          <p className="eyebrow">
            Application error
          </p>

          <h1>
            MIRA could not render this page
          </h1>

          <p>
            Reload the application. Unsaved form
            input on the current page will be lost.
          </p>

          {import.meta.env.DEV && (
            <details>
              <summary>
                Development error details
              </summary>

              <pre>
                {error.message}
              </pre>
            </details>
          )}

          <div className="error-boundary-actions">
            <button
              className="button button--primary"
              type="button"
              onClick={
                this.reloadApplication
              }
            >
              Reload MIRA
            </button>

            <a
              className="button button--secondary"
              href="/"
            >
              Return to overview
            </a>
          </div>
        </section>
      </main>
    );
  }
}