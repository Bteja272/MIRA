import {
  useState,
} from "react";
import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  getDocuments,
} from "../api/documents";
import {
  buildMedicalTimeline,
  compareMedicalDocuments,
  deleteIntelligence,
  generateIntelligence,
  getIntelligenceOrNull,
} from "../api/intelligence";
import {
  ApiError,
} from "../api/http";
import {
  StatusBanner,
} from "../components/StatusBanner";
import type {
  IntelligenceCompareResponse,
  IntelligenceTimelineResponse,
} from "../types/intelligence";
import "../styles/intelligence.css";


function humanize(
  value: string,
): string {
  return value
    .split("_")
    .map(
      (part) =>
        part.charAt(0).toUpperCase()
        + part.slice(1),
    )
    .join(" ");
}


function formatDate(
  value: string | null,
): string {
  if (!value) {
    return "Date not documented";
  }

  const date = new Date(value);

  if (
    Number.isNaN(
      date.getTime(),
    )
  ) {
    return value;
  }

  return new Intl.DateTimeFormat(
    undefined,
    {
      dateStyle: "medium",
    },
  ).format(date);
}


export function MedicalIntelligencePage() {
  const queryClient =
    useQueryClient();

  const [
    selectedDocumentId,
    setSelectedDocumentId,
  ] = useState("");

  const [
    longitudinalIds,
    setLongitudinalIds,
  ] = useState<string[]>([]);

  const [
    actionMessage,
    setActionMessage,
  ] = useState<string | null>(
    null,
  );

  const [
    timelineResult,
    setTimelineResult,
  ] = useState<
    IntelligenceTimelineResponse | null
  >(null);

  const [
    comparisonResult,
    setComparisonResult,
  ] = useState<
    IntelligenceCompareResponse | null
  >(null);

  const documentsQuery = useQuery({
    queryKey: ["documents"],
    queryFn: getDocuments,
  });

  const intelligenceQuery = useQuery({
    queryKey: [
      "medical-intelligence",
      selectedDocumentId,
    ],
    queryFn: () =>
      getIntelligenceOrNull(
        selectedDocumentId,
      ),
    enabled:
      selectedDocumentId.length > 0,
  });

  const generateMutation =
    useMutation({
      mutationFn: ({
        documentId,
        replaceExisting,
      }: {
        documentId: string;
        replaceExisting: boolean;
      }) =>
        generateIntelligence(
          documentId,
          replaceExisting,
        ),
      onSuccess: (
        response,
      ) => {
        queryClient.setQueryData(
          [
            "medical-intelligence",
            response.result.document_id,
          ],
          response.result,
        );

        setActionMessage(
          response.message,
        );
      },
    });

  const deleteMutation =
    useMutation({
      mutationFn: (
        documentId: string,
      ) =>
        deleteIntelligence(
          documentId,
        ),
      onSuccess: (
        response,
      ) => {
        queryClient.setQueryData(
          [
            "medical-intelligence",
            response.document_id,
          ],
          null,
        );

        setActionMessage(
          response.message,
        );
      },
    });

  const longitudinalMutation =
    useMutation({
      mutationFn: async (
        documentIds: string[],
      ) => {
        const timeline =
          await buildMedicalTimeline(
            documentIds,
          );

        const comparison =
          documentIds.length >= 2
            ? await compareMedicalDocuments(
              documentIds,
            )
            : null;

        return {
          timeline,
          comparison,
        };
      },
      onSuccess: ({
        timeline,
        comparison,
      }) => {
        setTimelineResult(
          timeline,
        );

        setComparisonResult(
          comparison,
        );
      },
    });

  const documents =
    documentsQuery.data?.documents
    ?? [];

  const persisted =
    intelligenceQuery.data
    ?? null;

  const intelligence =
    persisted?.intelligence
    ?? null;

  const stale =
    intelligenceQuery.error
      instanceof ApiError
    && intelligenceQuery.error.status
      === 409;

  const loadError =
    intelligenceQuery.isError
    && !stale
      ? (
        intelligenceQuery.error
          instanceof ApiError
          ? intelligenceQuery
            .error
            .message
          : (
            "Medical intelligence "
            + "could not be loaded."
          )
      )
      : null;

  const generationError =
    generateMutation.isError
      ? (
        generateMutation.error
          instanceof ApiError
          ? generateMutation
            .error
            .message
          : (
            "Medical intelligence "
            + "could not be generated."
          )
      )
      : null;

  function toggleLongitudinal(
    documentId: string,
  ): void {
    setLongitudinalIds(
      (current) => {
        if (
          current.includes(
            documentId,
          )
        ) {
          return current.filter(
            (value) =>
              value !== documentId,
          );
        }

        if (current.length >= 5) {
          return current;
        }

        return [
          ...current,
          documentId,
        ];
      },
    );
  }

  return (
    <section className="page-stack">
      <header className="page-header">
        <div>
          <p className="eyebrow">
            Document understanding
          </p>

          <h2>
            Medical intelligence
          </h2>

          <p>
            Understand documented findings,
            review safe general guidance, and
            compare selected records over time.
          </p>
        </div>

        {persisted && (
          <span className="connection-badge">
            {humanize(
              persisted.status,
            )}
          </span>
        )}
      </header>

      <section className="extraction-control-panel">
        <label
          className="field"
          htmlFor="intelligence-document"
        >
          <span>
            Select a document
          </span>

          <select
            id="intelligence-document"
            value={
              selectedDocumentId
            }
            onChange={(event) => {
              setSelectedDocumentId(
                event.target.value,
              );

              setActionMessage(
                null,
              );

              generateMutation.reset();
              deleteMutation.reset();
            }}
          >
            <option value="">
              Choose an uploaded document
            </option>

            {documents.map(
              (document) => (
                <option
                  key={
                    document.document_id
                  }
                  value={
                    document.document_id
                  }
                >
                  {document.filename}
                  {" · "}
                  {humanize(
                    document.document_type
                    ?? "unknown",
                  )}
                </option>
              ),
            )}
          </select>
        </label>

        <div className="extraction-actions">
          {!persisted ? (
            <button
              type="button"
              className="button button--primary"
              disabled={
                !selectedDocumentId
                || generateMutation.isPending
              }
              onClick={() => {
                if (
                  selectedDocumentId
                ) {
                  generateMutation.mutate({
                    documentId:
                      selectedDocumentId,
                    replaceExisting:
                      stale,
                  });
                }
              }}
            >
              {generateMutation.isPending
                ? (
                  "Building intelligence…"
                )
                : stale
                  ? (
                    "Regenerate intelligence"
                  )
                  : (
                    "Generate intelligence"
                  )}
            </button>
          ) : (
            <>
              <button
                type="button"
                className="button button--secondary"
                disabled={
                  intelligenceQuery.isFetching
                }
                onClick={() => {
                  void intelligenceQuery.refetch();
                }}
              >
                Refresh
              </button>

              <button
                type="button"
                className="button button--primary"
                disabled={
                  generateMutation.isPending
                }
                onClick={() => {
                  generateMutation.mutate({
                    documentId:
                      selectedDocumentId,
                    replaceExisting: true,
                  });
                }}
              >
                Regenerate
              </button>

              <button
                type="button"
                className="button button--danger"
                disabled={
                  deleteMutation.isPending
                }
                onClick={() => {
                  deleteMutation.mutate(
                    selectedDocumentId,
                  );
                }}
              >
                Delete intelligence
              </button>
            </>
          )}
        </div>
      </section>

      {generateMutation.isPending && (
        <section
          className="extraction-progress"
          role="status"
          aria-live="polite"
        >
          <div className="query-spinner" />

          <div>
            <strong>
              Preparing medical intelligence…
            </strong>

            <p>
              MIRA may generate a structured
              extraction first if this document
              does not already have one.
            </p>
          </div>
        </section>
      )}

      {stale && (
        <StatusBanner tone="info">
          The structured extraction changed
          after this intelligence result was
          generated. Regenerate intelligence
          before using it.
        </StatusBanner>
      )}

      {actionMessage && (
        <StatusBanner tone="success">
          {actionMessage}
        </StatusBanner>
      )}

      {generationError && (
        <StatusBanner tone="error">
          {generationError}
        </StatusBanner>
      )}

      {loadError && (
        <StatusBanner tone="error">
          {loadError}
        </StatusBanner>
      )}

      {!selectedDocumentId && (
        <section className="answer-empty">
          <h3>
            Select a document
          </h3>

          <p>
            Medical intelligence begins with
            one uploaded medical record.
          </p>
        </section>
      )}

      {selectedDocumentId
        && !intelligenceQuery.isLoading
        && !persisted
        && !stale
        && !generateMutation.isPending && (
          <section className="answer-empty">
            <h3>
              No stored intelligence
            </h3>

            <p>
              Generate medical intelligence to
              normalize documented findings,
              build a record timeline, and show
              bounded educational guidance.
            </p>
          </section>
        )}

      {intelligence && (
        <section className="intelligence-stack">
          {intelligence.warnings.length > 0 && (
            <section className="extraction-warning-panel">
              <div>
                <p className="eyebrow">
                  Intelligence limitations
                </p>

                <h3>
                  Limited source information
                </h3>
              </div>

              <ul>
                {intelligence.warnings.map(
                  (warning) => (
                    <li key={warning}>
                      {warning}
                    </li>
                  ),
                )}
              </ul>
            </section>
          )}

          <section className="extraction-section">
            <div className="section-heading">
              <div>
                <p className="eyebrow">
                  Normalized concepts
                </p>

                <h3>
                  Medical entities
                </h3>
              </div>

              <span>
                {
                  intelligence
                    .normalized_entities
                    .length
                }
              </span>
            </div>

            {intelligence
              .normalized_entities
              .length === 0 ? (
                <div className="extraction-empty">
                  No normalized medical
                  entities were available.
                </div>
              ) : (
                <div className="intelligence-grid">
                  {intelligence
                    .normalized_entities
                    .map(
                      (entity, index) => (
                        <article
                          className="intelligence-card"
                          key={
                            entity.canonical_key
                            + index
                          }
                        >
                          <span className="route-badge">
                            {humanize(
                              entity.entity_type,
                            )}
                          </span>

                          <h4>
                            {
                              entity
                                .normalized_name
                            }
                          </h4>

                          {entity.raw_name
                            !== entity
                              .normalized_name && (
                            <p>
                              <strong>
                                Document text:
                              </strong>
                              {" "}
                              {
                                entity.raw_name
                              }
                            </p>
                          )}

                          {entity.status && (
                            <p>
                              <strong>
                                Documented status:
                              </strong>
                              {" "}
                              {
                                humanize(
                                  entity.status,
                                )
                              }
                            </p>
                          )}

                          {entity.code && (
                            <p>
                              <strong>
                                Documented code:
                              </strong>
                              {" "}
                              {entity.code}
                            </p>
                          )}
                        </article>
                      ),
                    )}
                </div>
              )}
          </section>

          <section className="extraction-section">
            <div className="section-heading">
              <div>
                <p className="eyebrow">
                  Document understanding
                </p>

                <h3>
                  Explanations and guidance
                </h3>
              </div>

              <span>
                {
                  intelligence
                    .guidance_cards
                    .length
                }
              </span>
            </div>

            {intelligence
              .guidance_cards
              .length === 0 ? (
                <div className="extraction-empty">
                  No documented diagnosis or
                  supported injury topic produced
                  a guidance card.
                </div>
              ) : (
                <div className="intelligence-guidance-list">
                  {intelligence
                    .guidance_cards
                    .map(
                      (card) => (
                        <article
                          className="guidance-card"
                          key={card.topic}
                        >
                          <header>
                            <div>
                              <p className="eyebrow">
                                Documented fact
                              </p>

                              <h4>
                                {card.topic}
                              </h4>
                            </div>

                            <span className="route-badge">
                              {humanize(
                                card.guidance_level,
                              )}
                            </span>
                          </header>

                          <p>
                            <strong>
                              {
                                card
                                  .documented_fact
                                  .label
                              }:
                            </strong>
                            {" "}
                            {
                              card
                                .documented_fact
                                .value
                            }
                          </p>

                          <div className="guidance-block">
                            <h5>
                              What it means
                            </h5>

                            <p>
                              {
                                card
                                  .plain_language_explanation
                              }
                            </p>
                          </div>

                          {card
                            .general_information
                            .length > 0 && (
                              <div className="guidance-block">
                                <h5>
                                  General information
                                </h5>

                                <ul>
                                  {card
                                    .general_information
                                    .map(
                                      (item) => (
                                        <li key={item}>
                                          {item}
                                        </li>
                                      ),
                                    )}
                                </ul>
                              </div>
                            )}

                          {card
                            .supportive_care
                            .length > 0 && (
                              <div className="guidance-block">
                                <h5>
                                  Supportive guidance
                                </h5>

                                <ul>
                                  {card
                                    .supportive_care
                                    .map(
                                      (item) => (
                                        <li key={item}>
                                          {item}
                                        </li>
                                      ),
                                    )}
                                </ul>
                              </div>
                            )}

                          {card
                            .red_flags
                            .length > 0 && (
                              <div className="guidance-block guidance-block--warning">
                                <h5>
                                  Red flags
                                </h5>

                                <ul>
                                  {card
                                    .red_flags
                                    .map(
                                      (item) => (
                                        <li key={item}>
                                          {item}
                                        </li>
                                      ),
                                    )}
                                </ul>

                                {card
                                  .when_to_seek_care && (
                                    <p>
                                      {
                                        card
                                          .when_to_seek_care
                                      }
                                    </p>
                                  )}
                              </div>
                            )}

                          {card
                            .questions_for_clinician
                            .length > 0 && (
                              <div className="guidance-block">
                                <h5>
                                  Questions for your
                                  clinician
                                </h5>

                                <ul>
                                  {card
                                    .questions_for_clinician
                                    .map(
                                      (item) => (
                                        <li key={item}>
                                          {item}
                                        </li>
                                      ),
                                    )}
                                </ul>
                              </div>
                            )}
                        </article>
                      ),
                    )}
                </div>
              )}
          </section>

          <section className="extraction-section">
            <div className="section-heading">
              <div>
                <p className="eyebrow">
                  This document
                </p>

                <h3>
                  Document timeline
                </h3>
              </div>

              <span>
                {
                  intelligence
                    .timeline_events
                    .length
                }
              </span>
            </div>

            <div className="timeline-list">
              {intelligence
                .timeline_events
                .map(
                  (event) => (
                    <article
                      className="timeline-card"
                      key={event.event_id}
                    >
                      <div>
                        <strong>
                          {event.title}
                        </strong>

                        <span>
                          {humanize(
                            event.event_type,
                          )}
                        </span>
                      </div>

                      <time>
                        {formatDate(
                          event.event_date,
                        )}
                      </time>

                      {event.detail && (
                        <p>
                          {event.detail}
                        </p>
                      )}
                    </article>
                  ),
                )}
            </div>
          </section>
        </section>
      )}

      <section className="extraction-section">
        <div className="section-heading">
          <div>
            <p className="eyebrow">
              Longitudinal intelligence
            </p>

            <h3>
              Compare records over time
            </h3>
          </div>

          <span>
            {longitudinalIds.length}
            {" selected"}
          </span>
        </div>

        <p>
          Select up to five records. MIRA reports
          documentary differences without deciding
          whether they represent improvement,
          worsening, treatment success, or causation.
        </p>

        <div className="intelligence-document-picker">
          {documents.map(
            (document) => (
              <label
                key={
                  document.document_id
                }
              >
                <input
                  type="checkbox"
                  checked={
                    longitudinalIds.includes(
                      document.document_id,
                    )
                  }
                  disabled={
                    !longitudinalIds.includes(
                      document.document_id,
                    )
                    && longitudinalIds.length
                      >= 5
                  }
                  onChange={() =>
                    toggleLongitudinal(
                      document.document_id,
                    )
                  }
                />

                <span>
                  {document.filename}
                </span>
              </label>
            ),
          )}
        </div>

        <button
          type="button"
          className="button button--primary"
          disabled={
            longitudinalIds.length === 0
            || longitudinalMutation.isPending
          }
          onClick={() => {
            longitudinalMutation.mutate(
              longitudinalIds,
            );
          }}
        >
          {longitudinalMutation.isPending
            ? "Building longitudinal view…"
            : "Build longitudinal view"}
        </button>

        {longitudinalMutation.isError && (
          <StatusBanner tone="error">
            The selected records could not
            be analyzed longitudinally.
          </StatusBanner>
        )}

        {timelineResult && (
          <section className="longitudinal-result">
            <h4>
              Combined timeline
            </h4>

            {timelineResult.notices.map(
              (notice) => (
                <p
                  className="intelligence-notice"
                  key={notice}
                >
                  {notice}
                </p>
              ),
            )}

            <div className="timeline-list">
              {timelineResult.events.map(
                (event) => (
                  <article
                    className="timeline-card"
                    key={
                      event.event_id
                      + event.document_id
                    }
                  >
                    <div>
                      <strong>
                        {event.title}
                      </strong>

                      <span>
                        {humanize(
                          event.event_type,
                        )}
                      </span>
                    </div>

                    <time>
                      {formatDate(
                        event.event_date,
                      )}
                    </time>

                    {event.detail && (
                      <p>
                        {event.detail}
                      </p>
                    )}
                  </article>
                ),
              )}
            </div>
          </section>
        )}

        {comparisonResult && (
          <section className="longitudinal-result">
            <h4>
              Documented changes
            </h4>

            {comparisonResult.notices.map(
              (notice) => (
                <p
                  className="intelligence-notice"
                  key={notice}
                >
                  {notice}
                </p>
              ),
            )}

            {comparisonResult.changes.length
              === 0 ? (
                <div className="extraction-empty">
                  No supported documentary
                  differences were detected.
                </div>
              ) : (
                <div className="intelligence-guidance-list">
                  {comparisonResult
                    .changes
                    .map(
                      (change, index) => (
                        <article
                          className="intelligence-card"
                          key={
                            change.canonical_key
                            + change.change_type
                            + index
                          }
                        >
                          <span className="route-badge">
                            {humanize(
                              change.change_type,
                            )}
                          </span>

                          <h4>
                            {
                              change
                                .normalized_name
                            }
                          </h4>

                          <p>
                            {
                              change.description
                            }
                          </p>

                          {change
                            .before_summary && (
                              <p>
                                <strong>
                                  Earlier:
                                </strong>
                                {" "}
                                {
                                  change
                                    .before_summary
                                }
                              </p>
                            )}

                          {change
                            .after_summary && (
                              <p>
                                <strong>
                                  Later:
                                </strong>
                                {" "}
                                {
                                  change
                                    .after_summary
                                }
                              </p>
                            )}
                        </article>
                      ),
                    )}
                </div>
              )}
          </section>
        )}
      </section>

      <section className="safety-panel">
        <div>
          <p className="eyebrow">
            Medical intelligence boundary
          </p>

          <h3>
            Education, not diagnosis or treatment
          </h3>
        </div>

        <p>
          Documented facts come from the structured
          extraction. General information and
          supportive guidance are labeled separately.
          MIRA does not diagnose from symptoms,
          prescribe treatment, change medications,
          provide medication dosing, or predict
          outcomes.
        </p>
      </section>
    </section>
  );
}