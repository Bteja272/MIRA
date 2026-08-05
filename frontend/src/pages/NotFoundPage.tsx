import {
  Link,
} from "react-router";

export function NotFoundPage() {
  return (
    <main
      id="main-content"
      className="centered-page"
      tabIndex={-1}
    >
      <section className="not-found-card">
        <p className="eyebrow">404</p>

        <h1>Page not found</h1>

        <p>
          The requested MIRA page does not exist.
        </p>

        <Link
          className="button button--primary"
          to="/"
        >
          Return to overview
        </Link>
      </section>
    </main>
  );
}