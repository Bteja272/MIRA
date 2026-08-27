import {
  useEffect,
  useRef,
  useState,
  type FormEvent,
} from "react";
import {
  useMutation,
  useQuery,
} from "@tanstack/react-query";

import { getDocuments } from "../api/documents";
import { ApiError } from "../api/http";
import { queryMira } from "../api/query";
import { DocumentSelector } from "../components/DocumentSelector";
import { SourceCard } from "../components/SourceCard";
import { StatusBanner } from "../components/StatusBanner";
import type { QueryResponse } from "../types/query";
import "../styles/query.css";

const MAX_SELECTED_DOCUMENTS = 5;
const MAX_QUERY_CHARACTERS = 4000;

function elapsedLabel(
  elapsedSeconds: number,
): string {
  if (elapsedSeconds < 10) {
    return "MIRA is preparing the request…";
  }

  if (elapsedSeconds < 30) {
    return (
      "MIRA is retrieving relevant context "
      + "and generating a grounded answer…"
    );
  }

  return (
    "The local model is still working. "
    + "Complex document questions may take a minute or longer."
  );
}

function routeLabel(
  route: string,
): string {
  switch (route) {
    case "rag":
      return "Document-grounded";
    case "direct":
      return "General education";
    case "web":
      return "Current web context";
    case "safety_guard":
      return "Safety response";
    default:
      return route;
  }
}

export function AskMiraPage() {
  const [question, setQuestion] = useState("");
  const [selectedDocumentIds, setSelectedDocumentIds] = useState<string[]>([]);
  const [result, setResult] = useState<QueryResponse | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const abortControllerRef = useRef<AbortController | null>(null);

  const documentsQuery = useQuery({
    queryKey: ["documents"],
    queryFn: getDocuments,
  });

  const queryMutation = useMutation({
    mutationFn: async () => {
      const controller = new AbortController();
      abortControllerRef.current = controller;

      return queryMira(
        {
          query: question.trim(),
          document_ids:
            selectedDocumentIds.length > 0
              ? selectedDocumentIds
              : undefined,
          conversation_id:
            conversationId ?? undefined,
        },
        controller.signal,
      );
    },
    onMutate: () => {
      setResult(null);
      setElapsedSeconds(0);
    },
    onSuccess: (response) => {
      setResult(response);
      setConversationId(
      response.conversation_id,
  );
    },
    onSettled: () => {
      abortControllerRef.current = null;
    },
  });

  useEffect(() => {
    if (!queryMutation.isPending) {
      return;
    }

    const intervalId = window.setInterval(
      () => {
        setElapsedSeconds((current) => current + 1);
      },
      1000,
    );

    return () => {
      window.clearInterval(intervalId);
    };
  }, [queryMutation.isPending]);

  const documents = documentsQuery.data?.documents ?? [];
  const trimmedQuestion = question.trim();
  const charactersRemaining = MAX_QUERY_CHARACTERS - question.length;
  const mutationError = queryMutation.error;

  const errorMessage =
    mutationError instanceof ApiError
      ? mutationError.message
      : mutationError instanceof DOMException
        && mutationError.name === "AbortError"
        ? "The request was cancelled."
        : queryMutation.isError
          ? "MIRA could not complete the request."
          : null;

  function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ): void {
    event.preventDefault();

    if (!trimmedQuestion) {
      return;
    }

    queryMutation.mutate();
  }

  function cancelRequest(): void {
    abortControllerRef.current?.abort();
  }

  return (
    <section className="page-stack">
      <header className="page-header">
        <div>
          <p className="eyebrow">Grounded question answering</p>
          <h2>Ask MIRA</h2>
          <p>
            Select up to five owned documents for a source-grounded answer,
            or leave the selection empty for a general educational question.
          </p>
        </div>

        <span className="connection-badge">
          {selectedDocumentIds.length} / {MAX_SELECTED_DOCUMENTS} selected
        </span>
      </header>

      <div className="query-layout">
        <aside className="query-sidebar">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Context</p>
              <h3>Select documents</h3>
            </div>

            {selectedDocumentIds.length > 0 && (
              <button
                className="text-button"
                type="button"
                disabled={queryMutation.isPending}
                onClick={() => setSelectedDocumentIds([])}
              >
                Clear
              </button>
            )}
          </div>

          {documentsQuery.isLoading && (
            <div className="selector-empty" role="status">
              Loading documents…
            </div>
          )}

          {documentsQuery.isError && (
            <StatusBanner tone="error">
              {documentsQuery.error instanceof ApiError
                ? documentsQuery.error.message
                : "The document list could not be loaded."}
            </StatusBanner>
          )}

          {!documentsQuery.isLoading && !documentsQuery.isError && (
            <DocumentSelector
              documents={documents}
              selectedIds={selectedDocumentIds}
              maximumSelected={MAX_SELECTED_DOCUMENTS}
              disabled={queryMutation.isPending}
              onChange={setSelectedDocumentIds}
            />
          )}

          <div className="query-context-note">
            {selectedDocumentIds.length > 0
              ? (
                "MIRA will answer from the selected document context "
                + "and return supporting sources."
              )
              : (
                "No document is selected. MIRA will route the question "
                + "to general education or current web context when configured."
              )}
          </div>
        </aside>

        <main className="query-workspace">
          <form className="question-form" onSubmit={handleSubmit}>
            <label className="field" htmlFor="mira-question">
              <span>Your question</span>
              <textarea
                id="mira-question"
                rows={7}
                maxLength={MAX_QUERY_CHARACTERS}
                value={question}
                disabled={queryMutation.isPending}
                placeholder={
                  selectedDocumentIds.length > 0
                    ? (
                      "Example: What medications and follow-up "
                      + "instructions are listed?"
                    )
                    : (
                      "Example: What is the difference between systolic "
                      + "and diastolic blood pressure?"
                    )
                }
                onChange={(event) => setQuestion(event.target.value)}
              />
            </label>

            <div className="question-form__footer">
              <span
                className={
                  charactersRemaining < 200
                    ? "character-count character-count--warning"
                    : "character-count"
                }
              >
                {charactersRemaining} characters remaining
              </span>

              <div className="question-actions">
                {queryMutation.isPending && (
                  <button
                    className="button button--secondary"
                    type="button"
                    onClick={cancelRequest}
                  >
                    Cancel
                  </button>
                )}

                <button
                  className="button button--primary"
                  type="submit"
                  disabled={!trimmedQuestion || queryMutation.isPending}
                >
                  {queryMutation.isPending ? "Asking MIRA…" : "Ask MIRA"}
                </button>
              </div>
            </div>
          </form>

          {queryMutation.isPending && (
            <section className="query-progress" role="status" aria-live="polite">
              <div className="query-spinner" />
              <div>
                <strong>{elapsedLabel(elapsedSeconds)}</strong>
                <p>Elapsed time: {elapsedSeconds} seconds</p>
              </div>
            </section>
          )}

          {errorMessage && (
            <StatusBanner tone="error">{errorMessage}</StatusBanner>
          )}

          {!queryMutation.isPending && !result && !errorMessage && (
            <section className="answer-empty">
              <h3>No answer generated yet</h3>
              <p>
                Enter a question and optionally select documents. The answer
                and supporting sources will appear here.
              </p>
            </section>
          )}

          {result && (
            <section className="answer-panel">
              <header className="answer-panel__header">
                <div>
                  <p className="eyebrow">MIRA response</p>
                  <h3>{routeLabel(result.route)}</h3>
                </div>
                <span className="route-badge">{result.route}</span>
              </header>

              {result.route === "safety_guard" && (
                <StatusBanner tone="info">
                  This response was produced by MIRA&apos;s medical safety guard.
                  {result.safety_category
                    ? ` Category: ${result.safety_category}.`
                    : ""}
                </StatusBanner>
              )}

              <div className="answer-text">
                {result.answer
                  ? result.answer.split(/\n{2,}/).map((paragraph, index) => (
                    <p key={`${index}-${paragraph.slice(0, 20)}`}>
                      {paragraph}
                    </p>
                  ))
                  : <p>MIRA returned no answer text.</p>}
              </div>

              <div className="answer-summary">
                <span>
                  {result.selected_document_count} document
                  {result.selected_document_count === 1 ? "" : "s"} used
                </span>
                <span>
                  {result.sources.length} source
                  {result.sources.length === 1 ? "" : "s"}
                </span>
              </div>

              {result.sources.length > 0 && (
                <section className="sources-section">
                  <div>
                    <p className="eyebrow">Supporting context</p>
                    <h4>Sources</h4>
                  </div>

                  <div className="source-list">
                    {result.sources.map((source, index) => (
                      <SourceCard
                        key={String(source.chunk_id ?? index)}
                        source={source}
                        index={index}
                      />
                    ))}
                  </div>
                </section>
              )}
            </section>
          )}
        </main>
      </div>

      <section className="safety-panel">
        <div>
          <p className="eyebrow">Medical safety</p>
          <h3>Educational support only</h3>
        </div>
        <p>
          MIRA does not diagnose, prescribe, or replace professional medical
          judgment. Document-grounded answers are limited to the uploaded text
          and should be reviewed with a licensed healthcare professional.
        </p>
      </section>
    </section>
  );
}