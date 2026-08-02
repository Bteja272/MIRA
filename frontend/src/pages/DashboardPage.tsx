import { Link } from "react-router";

import { useAuth } from "../auth/AuthProvider";

const cards = [
  {
    title: "Documents",
    body: (
      "Upload PDF or TXT medical documents, "
      + "review metadata, and permanently delete "
      + "stored records."
    ),
    phase: "Available",
    path: "/documents",
  },
  {
    title: "Ask MIRA",
    body: (
      "Select up to five owned documents and ask "
      + "source-grounded questions."
    ),
    phase: "Next: Batch 3C",
    path: null,
  },
  {
    title: "Structured extraction",
    body: (
      "Generate patient, diagnosis, medication, "
      + "provider, follow-up, and evidence fields."
    ),
    phase: "Next: Batch 3D",
    path: null,
  },
];

export function DashboardPage() {
  const { user } = useAuth();

  return (
    <section className="page-stack">
      <header className="page-header">
        <div>
          <p className="eyebrow">
            Frontend workspace
          </p>

          <h2>
            Backend-connected workspace
          </h2>

          <p>
            Signed in as {user?.email}.
            Authentication and protected routing
            are active.
          </p>
        </div>

        <span className="connection-badge">
          API session active
        </span>
      </header>

      <div className="feature-grid">
        {cards.map(
          (card) => (
            <article
              className="feature-card"
              key={card.title}
            >
              <span className="feature-card__phase">
                {card.phase}
              </span>

              <h3>{card.title}</h3>

              <p>{card.body}</p>

              {card.path && (
                <Link
                  className="feature-card__link"
                  to={card.path}
                >
                  Open documents
                </Link>
              )}
            </article>
          ),
        )}
      </div>

      <section className="safety-panel">
        <div>
          <p className="eyebrow">
            Development boundary
          </p>

          <h3>
            Use synthetic documents only
          </h3>
        </div>

        <p>
          MIRA is still a development system. Do not
          upload real patient information until
          production privacy, security, audit, and
          deployment controls are complete.
        </p>
      </section>
    </section>
  );
}