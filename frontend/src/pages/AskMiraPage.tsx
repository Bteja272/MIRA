import { useEffect, useRef, useState, type FormEvent } from "react";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  deleteConversation,
  getConversation,
  getConversations,
} from "../api/conversations";
import { getDocuments } from "../api/documents";
import { ApiError } from "../api/http";
import { queryMira } from "../api/query";
import { AssistantSpeechControls } from "../components/AssistantSpeechControls";
import { ConversationPanel } from "../components/ConversationPanel";
import { DocumentSelector } from "../components/DocumentSelector";
import { StatusBanner } from "../components/StatusBanner";
import type { ConversationMessage } from "../types/conversation";
import type { QueryResponse, QuerySource } from "../types/query";

import "../styles/query.css";

import {
  VoiceInputButton,
  type VoiceInputButtonHandle,
} from "../components/VoiceInputButton";
import {
  useSpeechSynthesis,
  type UseSpeechSynthesisResult,
} from "../hooks/useSpeechSynthesis";

const MAX_SELECTED_DOCUMENTS = 5;
const MAX_QUERY_CHARACTERS = 4000;

function elapsedLabel(elapsedSeconds: number): string {
  if (elapsedSeconds < 10) {
    return "MIRA is preparing " + "the request…";
  }

  if (elapsedSeconds < 30) {
    return (
      "MIRA is retrieving relevant " +
      "context and generating a " +
      "grounded answer…"
    );
  }

  return (
    "The local model is still working. " +
    "Complex document questions may " +
    "take a minute or longer."
  );
}

function routeLabel(route: string): string {
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

function errorMessageFrom(error: unknown, fallback: string): string {
  if (error instanceof ApiError) {
    return error.message;
  }

  if (error instanceof DOMException && error.name === "AbortError") {
    return "The request was cancelled.";
  }

  return fallback;
}

function sourceString(source: QuerySource, keys: string[]): string | null {
  for (const key of keys) {
    const value = source[key];
    if (typeof value === "string" && value.trim()) {
      return value.trim();
    }
  }
  return null;
}

function sourceNumber(source: QuerySource, keys: string[]): number | null {
  for (const key of keys) {
    const value = source[key];
    if (typeof value === "number" && Number.isFinite(value)) {
      return value;
    }
    if (typeof value === "string" && value.trim() && Number.isFinite(Number(value))) {
      return Number(value);
    }
  }
  return null;
}

function AnswerContent({
  content,
  sources,
  onSourceSelect,
}: {
  content: string;
  sources: QuerySource[];
  onSourceSelect: (index: number) => void;
}) {
  const paragraphs = content.split(/\n{2,}/);

  return (
    <div className="answer-text">
      {paragraphs.map((paragraph, paragraphIndex) => {
        const parts = paragraph.split(/(\[Source\s+\d+\])/gi);

        return (
          <p key={`${paragraphIndex}-${paragraph.slice(0, 20)}`}>
            {parts.map((part, partIndex) => {
              const match = part.match(/^\[Source\s+(\d+)\]$/i);
              if (!match) {
                return <span key={partIndex}>{part}</span>;
              }

              const sourceIndex = Number(match[1]) - 1;
              if (sourceIndex < 0 || sourceIndex >= sources.length) {
                return <span key={partIndex}>{part}</span>;
              }

              return (
                <button
                  key={partIndex}
                  type="button"
                  className="citation-badge"
                  aria-label={`Show source ${sourceIndex + 1}`}
                  onClick={() => onSourceSelect(sourceIndex)}
                >
                  {sourceIndex + 1}
                </button>
              );
            })}
          </p>
        );
      })}
    </div>
  );
}

function ConversationMessageCard({
  message,
  speech,
  onListen,
  onReplay,
  onSourceSelect,
}: {
  message: ConversationMessage;
  speech: UseSpeechSynthesisResult;
  onListen: (messageId: string, text: string) => void;
  onReplay: (messageId: string, text: string) => void;
  onSourceSelect: (index: number, sources: QuerySource[]) => void;
}) {
  return (
    <article
      className={
        "conversation-message " + `conversation-message--${message.role}`
      }
      data-testid={"conversation-message-" + message.role}
    >
      <header className={"conversation-message__header"}>
        <strong>{message.role === "user" ? "You" : "MIRA"}</strong>

        {message.route ? (
          <span className="route-badge">{message.route}</span>
        ) : null}
      </header>

      {message.role === "assistant" && message.route === "safety_guard" ? (
        <StatusBanner tone="info">
          This response was produced by MIRA&apos;s medical safety guard.
          {message.safety_category
            ? " Category: " + message.safety_category + "."
            : ""}
        </StatusBanner>
      ) : null}

      {message.content ? (
        <AnswerContent
          content={message.content}
          sources={message.sources}
          onSourceSelect={(index) => onSourceSelect(index, message.sources)}
        />
      ) : (
        <div className="answer-text">
          <p>MIRA returned no answer text.</p>
        </div>
      )}

      {message.role === "assistant" && message.content ? (
        <AssistantSpeechControls
          messageId={message.message_id}
          text={message.content}
          supported={speech.supported}
          state={speech.state}
          activeMessageId={speech.activeMessageId}
          lastSpokenMessageId={speech.lastSpokenMessageId}
          error={speech.error}
          onListen={onListen}
          onPause={speech.pause}
          onResume={speech.resume}
          onStop={speech.stop}
          onReplay={onReplay}
        />
      ) : null}
    </article>
  );
}

export function AskMiraPage() {
  const queryClient = useQueryClient();

  const speech = useSpeechSynthesis();

  const voiceInputRef = useRef<VoiceInputButtonHandle | null>(null);

  function stopSpeechPlayback(): void {
    speech.stop();

    /*
     * speechSynthesis owns a browser-global
     * playback queue. Cancel it directly at
     * conversation boundaries as a defensive
     * fallback in addition to hook state.
     */
    if (typeof window !== "undefined" && window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
  }

  function abortVoiceInput(): void {
    voiceInputRef.current?.abort();

    /*
     * The recognition hook also reports
     * false through onListeningChange,
     * but reset the page state defensively.
     */
    setVoiceListening(false);
  }

  function stopVoiceInteraction(): void {
    abortVoiceInput();

    stopSpeechPlayback();
  }

  function handleSpeechListen(messageId: string, text: string): void {
    /*
     * TTS takes ownership of the browser
     * audio interaction. Recognition must
     * be fully aborted first.
     */
    abortVoiceInput();

    speech.speak(messageId, text);
  }

  function handleSpeechReplay(messageId: string, text: string): void {
    abortVoiceInput();

    speech.replay(messageId, text);
  }

  const [question, setQuestion] = useState("");

  const [selectedDocumentIds, setSelectedDocumentIds] = useState<string[]>([]);

  const [activeConversationId, setActiveConversationId] = useState<
    string | null
  >(null);

  const [conversationMessages, setConversationMessages] = useState<
    ConversationMessage[]
  >([]);

  const [latestResult, setLatestResult] = useState<QueryResponse | null>(null);

  const [activeEvidenceIndex, setActiveEvidenceIndex] = useState(0);

  const [activeEvidenceSourcesOverride, setActiveEvidenceSourcesOverride] = useState<
    QuerySource[] | null
  >(null);

  const [conversationActionError, setConversationActionError] = useState<
    string | null
  >(null);

  const [deletingConversationId, setDeletingConversationId] = useState<
    string | null
  >(null);

  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  const [voiceListening, setVoiceListening] = useState(false);

  const abortControllerRef = useRef<AbortController | null>(null);

  const documentsQuery = useQuery({
    queryKey: ["documents"],
    queryFn: getDocuments,
  });

  const conversationsQuery = useQuery({
    queryKey: ["conversations"],
    queryFn: getConversations,
  });

  const loadConversationMutation = useMutation({
    mutationFn: (conversationId: string) => getConversation(conversationId),

    onSuccess: (conversation) => {
      setActiveConversationId(conversation.conversation_id);

      setConversationMessages(conversation.messages);

      setLatestResult(null);
      setActiveEvidenceIndex(0);
      setActiveEvidenceSourcesOverride(null);

      setConversationActionError(null);
    },

    onError: (error) => {
      setConversationActionError(
        errorMessageFrom(error, "The conversation " + "could not be loaded."),
      );
    },
  });

  const deleteConversationMutation = useMutation({
    mutationFn: (conversationId: string) => deleteConversation(conversationId),

    onSuccess: async (_data, conversationId) => {
      if (activeConversationId === conversationId) {
        setActiveConversationId(null);

        setConversationMessages([]);

        setLatestResult(null);

        setQuestion("");

        setSelectedDocumentIds([]);
      }

      setConversationActionError(null);

      await queryClient.invalidateQueries({
        queryKey: ["conversations"],
      });
    },

    onError: (error) => {
      setConversationActionError(
        errorMessageFrom(error, "The conversation " + "could not be deleted."),
      );
    },

    onSettled: () => {
      setDeletingConversationId(null);
    },
  });

  const queryMutation = useMutation({
    mutationFn: async () => {
      const controller = new AbortController();

      abortControllerRef.current = controller;

      return queryMira(
        {
          query: question.trim(),

          document_ids:
            selectedDocumentIds.length > 0 ? selectedDocumentIds : undefined,

          conversation_id: activeConversationId ?? undefined,
        },
        controller.signal,
      );
    },

    onMutate: () => {
      stopVoiceInteraction();

      setLatestResult(null);

      setElapsedSeconds(0);

      setConversationActionError(null);
    },

    onSuccess: async (response) => {
      setLatestResult(response);
      setActiveEvidenceIndex(0);
      setActiveEvidenceSourcesOverride(response.sources);

      setActiveConversationId(response.conversation_id);

      setQuestion("");

      try {
        const conversation = await getConversation(response.conversation_id);

        setConversationMessages(conversation.messages);
      } catch (error) {
        setConversationActionError(
          errorMessageFrom(
            error,
            "The answer was " +
              "generated, but the " +
              "conversation history " +
              "could not be refreshed.",
          ),
        );
      }

      await queryClient.invalidateQueries({
        queryKey: ["conversations"],
      });
    },

    onSettled: () => {
      abortControllerRef.current = null;
    },
  });

  useEffect(() => {
    if (!queryMutation.isPending) {
      return;
    }

    const intervalId = window.setInterval(() => {
      setElapsedSeconds((current) => current + 1);
    }, 1000);

    return () => {
      window.clearInterval(intervalId);
    };
  }, [queryMutation.isPending]);

  const documents = documentsQuery.data?.documents ?? [];

  const conversations = conversationsQuery.data?.conversations ?? [];

  const mostRecentAssistantWithSources = [...conversationMessages]
    .reverse()
    .find((message) => message.role === "assistant" && message.sources.length > 0);

  const evidenceSources = activeEvidenceSourcesOverride
    ?? (latestResult?.sources.length
      ? latestResult.sources
      : mostRecentAssistantWithSources?.sources ?? []);

  const activeEvidenceSource = evidenceSources[activeEvidenceIndex] ?? evidenceSources[0] ?? null;

  useEffect(() => {
    if (activeEvidenceIndex >= evidenceSources.length) {
      setActiveEvidenceIndex(0);
    }
  }, [activeEvidenceIndex, evidenceSources.length]);

  const trimmedQuestion = question.trim();

  const charactersRemaining = MAX_QUERY_CHARACTERS - question.length;

  const mutationError = queryMutation.error;

  const queryErrorMessage = queryMutation.isError
    ? errorMessageFrom(
        mutationError,
        "MIRA could not " + "complete the request.",
      )
    : null;

  const interfaceBusy =
    queryMutation.isPending ||
    loadConversationMutation.isPending ||
    deleteConversationMutation.isPending ||
    voiceListening;

  function handleVoiceTranscript(transcript: string): void {
    const cleanedTranscript = transcript.trim();

    if (!cleanedTranscript) {
      return;
    }

    setQuestion((currentQuestion) => {
      const separator = currentQuestion.trim() ? " " : "";

      const combined = currentQuestion + separator + cleanedTranscript;

      return combined.slice(0, MAX_QUERY_CHARACTERS);
    });
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();

    if (!trimmedQuestion || interfaceBusy || voiceListening) {
      return;
    }

    queryMutation.mutate();
  }

  function cancelRequest(): void {
    abortControllerRef.current?.abort();
  }

  function handleNewConversation(): void {
    if (interfaceBusy) {
      return;
    }

    stopVoiceInteraction();

    setActiveConversationId(null);

    setConversationMessages([]);

    setLatestResult(null);
    setActiveEvidenceIndex(0);
    setActiveEvidenceSourcesOverride(null);

    setQuestion("");

    setSelectedDocumentIds([]);

    setConversationActionError(null);
  }

  function handleSelectConversation(conversationId: string): void {
    if (interfaceBusy || conversationId === activeConversationId) {
      return;
    }

    stopVoiceInteraction();

    /*
     * Historical document IDs are
     * display metadata only.
     *
     * Resuming a conversation must not
     * silently reactivate documents from
     * a previous turn.
     */
    setSelectedDocumentIds([]);

    setLatestResult(null);
    setActiveEvidenceIndex(0);
    setActiveEvidenceSourcesOverride(null);

    setConversationActionError(null);

    loadConversationMutation.mutate(conversationId);
  }

  function handleDeleteConversation(conversationId: string): void {
    if (interfaceBusy) {
      return;
    }

    const confirmed = window.confirm(
      "Permanently delete this " +
        "conversation and all of " +
        "its stored messages?",
    );

    if (!confirmed) {
      return;
    }

    stopVoiceInteraction();

    setDeletingConversationId(conversationId);

    setConversationActionError(null);

    deleteConversationMutation.mutate(conversationId);
  }

  return (
    <section className="page-stack ask-page">
      <header className="page-header ask-page__header">
        <div>
          <p className="eyebrow">Grounded workspace</p>
          <h2>Ask MIRA</h2>
          <p>
            Ask questions, inspect supporting evidence, and keep document context explicit.
          </p>
        </div>

        <span className="connection-badge">
          {selectedDocumentIds.length}
          {" / "}
          {MAX_SELECTED_DOCUMENTS}
          {" selected"}
        </span>
      </header>

      <section className="query-control-strip">
        <div className="query-control-card query-control-card--conversations">
          <ConversationPanel
            conversations={conversations}
            activeConversationId={activeConversationId}
            loading={conversationsQuery.isLoading}
            disabled={interfaceBusy}
            deletingConversationId={deletingConversationId}
            onNewConversation={handleNewConversation}
            onSelectConversation={handleSelectConversation}
            onDeleteConversation={handleDeleteConversation}
          />

          {conversationsQuery.isError ? (
            <StatusBanner tone="error">
              {errorMessageFrom(
                conversationsQuery.error,
                "The conversation list could not be loaded.",
              )}
            </StatusBanner>
          ) : null}
        </div>

        <div className="query-control-card query-control-card--documents">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Context</p>
              <h3>Select documents</h3>
            </div>

            {selectedDocumentIds.length > 0 ? (
              <button
                className="text-button"
                type="button"
                disabled={interfaceBusy}
                onClick={() => setSelectedDocumentIds([])}
              >
                Clear
              </button>
            ) : null}
          </div>

          {documentsQuery.isLoading ? (
            <div className="selector-empty" role="status">
              Loading documents…
            </div>
          ) : null}

          {documentsQuery.isError ? (
            <StatusBanner tone="error">
              {documentsQuery.error instanceof ApiError
                ? documentsQuery.error.message
                : "The document list could not be loaded."}
            </StatusBanner>
          ) : null}

          {!documentsQuery.isLoading && !documentsQuery.isError ? (
            <DocumentSelector
              documents={documents}
              selectedIds={selectedDocumentIds}
              maximumSelected={MAX_SELECTED_DOCUMENTS}
              disabled={interfaceBusy}
              onChange={setSelectedDocumentIds}
            />
          ) : null}
        </div>
      </section>

      <div className="ask-split-workspace">
        <aside className="evidence-pane" aria-label="Supporting evidence">
          <header className="evidence-pane__header">
            <div>
              <p className="eyebrow">Document evidence</p>
              <h3>
                {activeEvidenceSource
                  ? sourceString(activeEvidenceSource, [
                      "title",
                      "source_filename",
                      "filename",
                      "source",
                      "document_name",
                    ]) ?? "Supporting passage"
                  : "Supporting passage"}
              </h3>
            </div>

            {evidenceSources.length > 0 ? (
              <span className="evidence-pane__count">
                {activeEvidenceIndex + 1} / {evidenceSources.length}
              </span>
            ) : null}
          </header>

          {activeEvidenceSource ? (
            <div className="evidence-document" key={activeEvidenceIndex}>
              <div className="evidence-document__meta">
                {sourceNumber(activeEvidenceSource, ["page_number", "page"]) !== null ? (
                  <span>
                    Page {sourceNumber(activeEvidenceSource, ["page_number", "page"])}
                  </span>
                ) : null}
                {sourceNumber(activeEvidenceSource, ["chunk_index", "index"]) !== null ? (
                  <span>
                    Chunk {sourceNumber(activeEvidenceSource, ["chunk_index", "index"])}
                  </span>
                ) : null}
              </div>

              <div className="evidence-document__paper">
                <mark className="evidence-highlight">
                  {sourceString(activeEvidenceSource, [
                    "quoted_text",
                    "content",
                    "text",
                    "chunk_text",
                  ]) ?? "MIRA returned source metadata without an evidence excerpt."}
                </mark>
              </div>

              <div className="evidence-source-tabs" aria-label="Available sources">
                {evidenceSources.map((source, index) => (
                  <button
                    type="button"
                    key={String(source.chunk_id ?? source.document_id ?? index)}
                    className={
                      index === activeEvidenceIndex
                        ? "evidence-source-tab evidence-source-tab--active"
                        : "evidence-source-tab"
                    }
                    aria-label={`Show source ${index + 1}`}
                    onClick={() => setActiveEvidenceIndex(index)}
                  >
                    {index + 1}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="evidence-empty">
              <div className="evidence-empty__icon">⌁</div>
              <h4>No evidence selected yet</h4>
              <p>
                {selectedDocumentIds.length > 0
                  ? "Ask a document-grounded question. Supporting passages will appear here."
                  : "Select a document for grounded Q&A, or ask a general educational question."}
              </p>
            </div>
          )}
        </aside>

        <main className="query-workspace query-chat-pane">
          <div className="chat-toolbar">
            <div>
              <p className="eyebrow">Conversation</p>
              <strong>
                {activeConversationId ? "Conversation memory enabled" : "New conversation"}
              </strong>
            </div>

            {activeConversationId ? (
              <button
                className="text-button"
                type="button"
                disabled={interfaceBusy}
                onClick={handleNewConversation}
              >
                Start new
              </button>
            ) : null}
          </div>

          {loadConversationMutation.isPending ? (
            <section className="query-progress" role="status">
              <div className="query-spinner" />
              <div>
                <strong>Loading conversation…</strong>
                <p>Restoring stored messages.</p>
              </div>
            </section>
          ) : null}

          {conversationActionError ? (
            <StatusBanner tone="error">{conversationActionError}</StatusBanner>
          ) : null}

          <section
            className="conversation-history"
            aria-label="Conversation history"
            aria-live="polite"
          >
            {conversationMessages.length > 0 ? (
              conversationMessages.map((message) => (
                <ConversationMessageCard
                  key={message.message_id}
                  message={message}
                  speech={speech}
                  onListen={handleSpeechListen}
                  onReplay={handleSpeechReplay}
                  onSourceSelect={(index, sources) => {
                    setActiveEvidenceSourcesOverride(sources);
                    setActiveEvidenceIndex(index);
                  }}
                />
              ))
            ) : (
              <div className="conversation-start">
                <div className="conversation-start__mark">M</div>
                <h3>Ask about your records</h3>
                <p>
                  MIRA keeps document selection explicit and shows supporting evidence beside the answer.
                </p>
              </div>
            )}
          </section>

          {latestResult ? (
            <section className="latest-response-meta">
              <div className="latest-response-meta__row">
                <span>{routeLabel(latestResult.route)}</span>
                <span>
                  {latestResult.sources.length} source
                  {latestResult.sources.length === 1 ? "" : "s"}
                </span>
              </div>

              {latestResult.sources.length > 0 ? (
                <div className="latest-response-sources" aria-label="Response sources">
                  {latestResult.sources.map((source, index) => (
                    <button
                      key={String(source.chunk_id ?? source.document_id ?? index)}
                      type="button"
                      className="citation-source-pill"
                      onClick={() => {
                        setActiveEvidenceSourcesOverride(latestResult.sources);
                        setActiveEvidenceIndex(index);
                      }}
                    >
                      <span>{index + 1}</span>
                      {sourceString(source, [
                        "source_filename",
                        "filename",
                        "title",
                        "source",
                      ]) ?? `Source ${index + 1}`}
                    </button>
                  ))}
                </div>
              ) : null}
            </section>
          ) : null}

          <form className="question-form" onSubmit={handleSubmit}>
            <label className="field question-field" htmlFor="mira-question">
              <span>Your question</span>
              <textarea
                id="mira-question"
                rows={4}
                maxLength={MAX_QUERY_CHARACTERS}
                value={question}
                disabled={interfaceBusy}
                placeholder={
                  selectedDocumentIds.length > 0
                    ? "Ask about the selected document…"
                    : "Ask MIRA a general educational question…"
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
                <VoiceInputButton
                  ref={voiceInputRef}
                  disabled={interfaceBusy}
                  onBeforeStart={stopSpeechPlayback}
                  onTranscript={handleVoiceTranscript}
                  onListeningChange={setVoiceListening}
                />

                {queryMutation.isPending ? (
                  <button
                    className="button button--secondary"
                    type="button"
                    onClick={cancelRequest}
                  >
                    Cancel
                  </button>
                ) : null}

                <button
                  className="button button--primary"
                  type="submit"
                  disabled={!trimmedQuestion || interfaceBusy || voiceListening}
                >
                  {queryMutation.isPending ? "Asking MIRA…" : "Ask MIRA"}
                </button>
              </div>
            </div>
          </form>

          {queryMutation.isPending ? (
            <section className="query-progress" role="status" aria-live="polite">
              <div className="query-spinner" />
              <div>
                <strong>{elapsedLabel(elapsedSeconds)}</strong>
                <p>Elapsed time: {elapsedSeconds} seconds</p>
              </div>
            </section>
          ) : null}

          {queryErrorMessage ? (
            <StatusBanner tone="error">{queryErrorMessage}</StatusBanner>
          ) : null}
        </main>
      </div>

      <p className="ask-safety-note">
        MIRA explains supplied documents for educational purposes and does not diagnose or recommend treatment changes.
      </p>
    </section>
  );
}
