import {
  Link,
} from "react-router";

import {
  useAuth,
} from "../auth/useAuth";

const cards = [
  {
    title: "Documents",
    body: "Upload, review, and manage your indexed medical records.",
    path: "/documents",
    linkLabel: "Open documents",
    icon: "document",
  },
  {
    title: "Ask MIRA",
    body: "Ask grounded questions about the documents you select.",
    path: "/ask",
    linkLabel: "Ask a question",
    icon: "chat",
  },
  {
    title: "Structured extraction",
    body: "Review extracted facts with supporting source evidence.",
    path: "/extractions",
    linkLabel: "Open extractions",
    icon: "extract",
  },
];

function CardIcon({
  name,
}: {
  name: string;
}) {
  if (name === "chat") {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M4 5.5A2.5 2.5 0 0 1 6.5 3h11A2.5 2.5 0 0 1 20 5.5v8a2.5 2.5 0 0 1-2.5 2.5H10l-5 4v-4.6A2.5 2.5 0 0 1 4 13.5z" />
      </svg>
    );
  }

  if (name === "extract") {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M8 5h12M8 12h12M8 19h12" />
        <path d="m3.5 5 1.2 1.2L6.8 4M3.5 12l1.2 1.2L6.8 11M3.5 19l1.2 1.2L6.8 18" />
      </svg>
    );
  }

  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M6 3h8l4 4v14H6z" />
      <path d="M14 3v5h5" />
      <path d="M9 12h6M9 16h6" />
    </svg>
  );
}

export function DashboardPage() {
  const {
    user,
  } = useAuth();

  return (
    <section className="page-stack dashboard-page">
      <header className="page-header page-header--compact">
        <div>
          <p className="eyebrow">
            Overview
          </p>

          <h2>Welcome back</h2>

          <p>
            Your medical records, grounded answers,
            and extracted facts in one workspace.
          </p>
        </div>

        <span className="connection-badge">
          Session active
        </span>
      </header>

      <section className="dashboard-summary" aria-label="Workspace summary">
        <div className="summary-tile">
          <span className="summary-tile__label">Documents</span>
          <strong>Private</strong>
        </div>
        <div className="summary-tile">
          <span className="summary-tile__label">Grounding</span>
          <strong>Source-backed</strong>
        </div>
        <div className="summary-tile">
          <span className="summary-tile__label">Account</span>
          <strong>{user?.email ?? "Signed in"}</strong>
        </div>
      </section>

      <div className="feature-grid">
        {cards.map((card) => (
          <article
            className="feature-card"
            key={card.title}
          >
            <span className="feature-card__icon">
              <CardIcon name={card.icon} />
            </span>

            <h3>{card.title}</h3>
            <p>{card.body}</p>

            <Link
              className="feature-card__link"
              to={card.path}
            >
              {card.linkLabel}
              <span aria-hidden="true">→</span>
            </Link>
          </article>
        ))}
      </div>

      <section className="safety-panel safety-panel--quiet">
        <div>
          <p className="eyebrow">
            Development boundary
          </p>
          <h3>Use synthetic medical records only</h3>
        </div>
        <p>
          MIRA is still a development system and is not
          ready for real protected health information.
        </p>
      </section>
    </section>
  );
}
