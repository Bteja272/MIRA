import {
  useEffect,
  useRef,
  useState,
  type FormEvent,
} from "react";

import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  deleteConversation,
  getConversation,
  getConversations,
} from "../api/conversations";
import {
  getDocuments,
} from "../api/documents";
import {
  ApiError,
} from "../api/http";
import {
  queryMira,
} from "../api/query";
import {
  AssistantSpeechControls,
} from "../components/AssistantSpeechControls";
import {
  ConversationPanel,
} from "../components/ConversationPanel";
import {
  DocumentSelector,
} from "../components/DocumentSelector";
import {
  SourceCard,
} from "../components/SourceCard";
import {
  StatusBanner,
} from "../components/StatusBanner";
import type {
  ConversationMessage,
} from "../types/conversation";
import type {
  QueryResponse,
} from "../types/query";

import "../styles/query.css";

import {
  VoiceInputButton,
} from "../components/VoiceInputButton";
import {
  useSpeechSynthesis,
  type UseSpeechSynthesisResult,
} from "../hooks/useSpeechSynthesis";

const MAX_SELECTED_DOCUMENTS = 5;
const MAX_QUERY_CHARACTERS = 4000;


function elapsedLabel(
  elapsedSeconds: number,
): string {
  if (elapsedSeconds < 10) {
    return (
      "MIRA is preparing "
      + "the request…"
    );
  }

  if (elapsedSeconds < 30) {
    return (
      "MIRA is retrieving relevant "
      + "context and generating a "
      + "grounded answer…"
    );
  }

  return (
    "The local model is still working. "
    + "Complex document questions may "
    + "take a minute or longer."
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


function errorMessageFrom(
  error: unknown,
  fallback: string,
): string {
  if (error instanceof ApiError) {
    return error.message;
  }

  if (
    error instanceof DOMException
    && error.name === "AbortError"
  ) {
    return (
      "The request was cancelled."
    );
  }

  return fallback;
}


function ConversationMessageCard({
  message,
  speech,
}: {
  message: ConversationMessage;
  speech: UseSpeechSynthesisResult;
}) {
  return (
    <article
      className={
        (
          "conversation-message "
          + `conversation-message--${message.role
          }`
        )
      }
      data-testid={
        (
          "conversation-message-"
          + message.role
        )
      }
    >
      <header
        className={
          "conversation-message__header"
        }
      >
        <strong>
          {message.role === "user"
            ? "You"
            : "MIRA"}
        </strong>

        {message.route ? (
          <span
            className="route-badge"
          >
            {message.route}
          </span>
        ) : null}
      </header>

      {(
        message.role === "assistant"
        && message.route
        === "safety_guard"
      ) ? (
        <StatusBanner tone="info">
          This response was produced
          by MIRA&apos;s medical safety
          guard.
          {message.safety_category
            ? (
              " Category: "
              + message
                .safety_category
              + "."
            )
            : ""}
        </StatusBanner>
      ) : null}

      <div className="answer-text">
        {message.content
          ? (
            message.content
              .split(/\n{2,}/)
              .map(
                (
                  paragraph,
                  index,
                ) => (
                  <p
                    key={
                      (
                        `${index}-`
                        + paragraph
                          .slice(
                            0,
                            20,
                          )
                      )
                    }
                  >
                    {paragraph}
                  </p>
                ),
              )
          )
          : (
            <p>
              MIRA returned no
              answer text.
            </p>
          )}
      </div>

      {(
        message.role === "assistant"
        && message.content
      ) ? (
        <AssistantSpeechControls
          messageId={
            message.message_id
          }
          text={
            message.content
          }
          supported={
            speech.supported
          }
          state={
            speech.state
          }
          activeMessageId={
            speech.activeMessageId
          }
          lastSpokenMessageId={
            speech.lastSpokenMessageId
          }
          error={
            speech.error
          }
          onListen={
            speech.speak
          }
          onPause={
            speech.pause
          }
          onResume={
            speech.resume
          }
          onStop={
            speech.stop
          }
          onReplay={
            speech.replay
          }
        />
      ) : null}
    </article>
  );
}


export function AskMiraPage() {
  const queryClient =
    useQueryClient();

  const speech =
    useSpeechSynthesis();
  function stopSpeechPlayback():
    void {
      speech.stop();

      /*
      * speechSynthesis owns a browser-global
      * playback queue. Cancel it directly at
      * conversation boundaries as a defensive
      * fallback in addition to hook state.
      */
      if (
        typeof window !== "undefined"
        && window.speechSynthesis
      ) {
        window.speechSynthesis
          .cancel();
      }
    }

  const [
    question,
    setQuestion,
  ] = useState("");

  const [
    selectedDocumentIds,
    setSelectedDocumentIds,
  ] = useState<string[]>([]);

  const [
    activeConversationId,
    setActiveConversationId,
  ] = useState<string | null>(
    null,
  );

  const [
    conversationMessages,
    setConversationMessages,
  ] = useState<
    ConversationMessage[]
  >([]);

  const [
    latestResult,
    setLatestResult,
  ] = useState<
    QueryResponse | null
  >(null);

  const [
    conversationActionError,
    setConversationActionError,
  ] = useState<
    string | null
  >(null);

  const [
    deletingConversationId,
    setDeletingConversationId,
  ] = useState<
    string | null
  >(null);

  const [
    elapsedSeconds,
    setElapsedSeconds,
  ] = useState(0);

    const [
    voiceListening,
    setVoiceListening,
  ] = useState(false);

  const abortControllerRef =
    useRef<
      AbortController | null
    >(null);


  const documentsQuery =
    useQuery({
      queryKey: [
        "documents",
      ],
      queryFn:
        getDocuments,
    });


  const conversationsQuery =
    useQuery({
      queryKey: [
        "conversations",
      ],
      queryFn:
        getConversations,
    });


  const loadConversationMutation =
    useMutation({
      mutationFn: (
        conversationId: string,
      ) => (
        getConversation(
          conversationId,
        )
      ),

      onSuccess: (
        conversation,
      ) => {
        setActiveConversationId(
          conversation
            .conversation_id,
        );

        setConversationMessages(
          conversation.messages,
        );

        setLatestResult(
          null,
        );

        setConversationActionError(
          null,
        );
      },

      onError: (
        error,
      ) => {
        setConversationActionError(
          errorMessageFrom(
            error,
            (
              "The conversation "
              + "could not be loaded."
            ),
          ),
        );
      },
    });


  const deleteConversationMutation =
    useMutation({
      mutationFn: (
        conversationId: string,
      ) => (
        deleteConversation(
          conversationId,
        )
      ),

      onSuccess: async (
        _data,
        conversationId,
      ) => {
        if (
          activeConversationId
          === conversationId
        ) {
          setActiveConversationId(
            null,
          );

          setConversationMessages(
            [],
          );

          setLatestResult(
            null,
          );

          setQuestion("");

          setSelectedDocumentIds(
            [],
          );
        }

        setConversationActionError(
          null,
        );

        await queryClient
          .invalidateQueries({
            queryKey: [
              "conversations",
            ],
          });
      },

      onError: (
        error,
      ) => {
        setConversationActionError(
          errorMessageFrom(
            error,
            (
              "The conversation "
              + "could not be deleted."
            ),
          ),
        );
      },

      onSettled: () => {
        setDeletingConversationId(
          null,
        );
      },
    });


  const queryMutation =
    useMutation({
      mutationFn: async () => {
        const controller =
          new AbortController();

        abortControllerRef.current =
          controller;

        return queryMira(
          {
            query:
              question.trim(),

            document_ids:
              selectedDocumentIds
                .length > 0
                ? selectedDocumentIds
                : undefined,

            conversation_id:
              activeConversationId
              ?? undefined,
          },
          controller.signal,
        );
      },

      onMutate: () => {
        stopSpeechPlayback();

        setLatestResult(
          null,
        );

        setElapsedSeconds(
          0,
        );

        setConversationActionError(
          null,
        );
      },

      onSuccess: async (
        response,
      ) => {
        setLatestResult(
          response,
        );

        setActiveConversationId(
          response
            .conversation_id,
        );

        setQuestion("");

        try {
          const conversation =
            await getConversation(
              response
                .conversation_id,
            );

          setConversationMessages(
            conversation.messages,
          );
        } catch (error) {
          setConversationActionError(
            errorMessageFrom(
              error,
              (
                "The answer was "
                + "generated, but the "
                + "conversation history "
                + "could not be refreshed."
              ),
            ),
          );
        }

        await queryClient
          .invalidateQueries({
            queryKey: [
              "conversations",
            ],
          });
      },

      onSettled: () => {
        abortControllerRef
          .current = null;
      },
    });


  useEffect(
    () => {
      if (
        !queryMutation.isPending
      ) {
        return;
      }

      const intervalId =
        window.setInterval(
          () => {
            setElapsedSeconds(
              (current) => (
                current + 1
              ),
            );
          },
          1000,
        );

      return () => {
        window.clearInterval(
          intervalId,
        );
      };
    },
    [
      queryMutation.isPending,
    ],
  );


  const documents =
    documentsQuery
      .data?.documents
    ?? [];

  const conversations =
    conversationsQuery
      .data?.conversations
    ?? [];

  const trimmedQuestion =
    question.trim();

  const charactersRemaining =
    MAX_QUERY_CHARACTERS
    - question.length;

  const mutationError =
    queryMutation.error;

  const queryErrorMessage = (
    queryMutation.isError
      ? errorMessageFrom(
        mutationError,
        (
          "MIRA could not "
          + "complete the request."
        ),
      )
      : null
  );

  const interfaceBusy = (
    queryMutation.isPending
    || loadConversationMutation
      .isPending
    || deleteConversationMutation
      .isPending
    || voiceListening
  );


  function handleVoiceTranscript(
      transcript: string,
    ): void {
      const cleanedTranscript =
        transcript.trim();

      if (!cleanedTranscript) {
        return;
      }

      setQuestion(
        (currentQuestion) => {
          const separator =
            currentQuestion.trim()
              ? " "
              : "";

          const combined =
            (
              currentQuestion
              + separator
              + cleanedTranscript
            );

          return combined.slice(
            0,
            MAX_QUERY_CHARACTERS,
          );
        },
      );
    }

  function handleSubmit(
    event:
      FormEvent<HTMLFormElement>,
  ): void {
    event.preventDefault();

    if (
      !trimmedQuestion
      || interfaceBusy
      || voiceListening
    ) {
      return;
    }

    queryMutation.mutate();
  }


  function cancelRequest():
    void {
    abortControllerRef
      .current
      ?.abort();
  }


  function handleNewConversation():
    void {
    if (interfaceBusy) {
      return;
    }

    stopSpeechPlayback();

    setActiveConversationId(
      null,
    );

    setConversationMessages(
      [],
    );

    setLatestResult(
      null,
    );

    setQuestion("");

    setSelectedDocumentIds(
      [],
    );

    setConversationActionError(
      null,
    );
  }


  function handleSelectConversation(
    conversationId: string,
  ): void {
    if (
      interfaceBusy
      || conversationId
      === activeConversationId
    ) {
      return;
    }

    stopSpeechPlayback();

    /*
     * Historical document IDs are
     * display metadata only.
     *
     * Resuming a conversation must not
     * silently reactivate documents from
     * a previous turn.
     */
    setSelectedDocumentIds(
      [],
    );

    setLatestResult(
      null,
    );

    setConversationActionError(
      null,
    );

    loadConversationMutation
      .mutate(
        conversationId,
      );
  }


  function handleDeleteConversation(
    conversationId: string,
  ): void {
    if (interfaceBusy) {
      return;
    }

    const confirmed =
      window.confirm(
        (
          "Permanently delete this "
          + "conversation and all of "
          + "its stored messages?"
        ),
      );

    if (!confirmed) {
      return;
    }

    stopSpeechPlayback();

    setDeletingConversationId(
      conversationId,
    );

    setConversationActionError(
      null,
    );

    deleteConversationMutation
      .mutate(
        conversationId,
      );
  }


  return (
    <section className="page-stack">
      <header className="page-header">
        <div>
          <p className="eyebrow">
            Grounded question answering
          </p>

          <h2>
            Ask MIRA
          </h2>

          <p>
            Select up to five owned
            documents for a
            source-grounded answer, or
            leave the selection empty
            for a general educational
            question.
          </p>
        </div>

        <span
          className="connection-badge"
        >
          {selectedDocumentIds.length}
          {" / "}
          {MAX_SELECTED_DOCUMENTS}
          {" selected"}
        </span>
      </header>


      <div className="query-layout">
        <aside className="query-sidebar">
          <ConversationPanel
            conversations={
              conversations
            }
            activeConversationId={
              activeConversationId
            }
            loading={
              conversationsQuery
                .isLoading
            }
            disabled={
              interfaceBusy
            }
            deletingConversationId={
              deletingConversationId
            }
            onNewConversation={
              handleNewConversation
            }
            onSelectConversation={
              handleSelectConversation
            }
            onDeleteConversation={
              handleDeleteConversation
            }
          />


          {conversationsQuery
            .isError ? (
            <StatusBanner tone="error">
              {errorMessageFrom(
                conversationsQuery
                  .error,
                (
                  "The conversation "
                  + "list could not "
                  + "be loaded."
                ),
              )}
            </StatusBanner>
          ) : null}


          <div
            className="section-heading"
          >
            <div>
              <p className="eyebrow">
                Context
              </p>

              <h3>
                Select documents
              </h3>
            </div>

            {selectedDocumentIds
              .length > 0 ? (
              <button
                className="text-button"
                type="button"
                disabled={
                  interfaceBusy
                }
                onClick={() => {
                  setSelectedDocumentIds(
                    [],
                  );
                }}
              >
                Clear
              </button>
            ) : null}
          </div>


          {documentsQuery
            .isLoading ? (
            <div
              className="selector-empty"
              role="status"
            >
              Loading documents…
            </div>
          ) : null}


          {documentsQuery
            .isError ? (
            <StatusBanner tone="error">
              {documentsQuery.error
                instanceof ApiError
                ? documentsQuery
                  .error.message
                : (
                  "The document list "
                  + "could not be loaded."
                )}
            </StatusBanner>
          ) : null}


          {(
            !documentsQuery
              .isLoading
            && !documentsQuery
              .isError
          ) ? (
            <DocumentSelector
              documents={
                documents
              }
              selectedIds={
                selectedDocumentIds
              }
              maximumSelected={
                MAX_SELECTED_DOCUMENTS
              }
              disabled={
                interfaceBusy
              }
              onChange={
                setSelectedDocumentIds
              }
            />
          ) : null}


          <div
            className={
              "query-context-note"
            }
          >
            {selectedDocumentIds
              .length > 0
              ? (
                "MIRA will answer from "
                + "the currently selected "
                + "document context and "
                + "return supporting "
                + "sources."
              )
              : (
                "No document is selected. "
                + "Conversation history "
                + "may provide continuity, "
                + "but previous documents "
                + "are not automatically "
                + "reused."
              )}
          </div>
        </aside>


        <main
          className="query-workspace"
        >
          {activeConversationId ? (
            <section
              className={
                "active-conversation-banner"
              }
            >
              <div>
                <p className="eyebrow">
                  Active conversation
                </p>

                <strong>
                  Conversation memory
                  enabled
                </strong>
              </div>

              <button
                className="text-button"
                type="button"
                disabled={
                  interfaceBusy
                }
                onClick={
                  handleNewConversation
                }
              >
                Start new
              </button>
            </section>
          ) : null}


          {loadConversationMutation
            .isPending ? (
            <section
              className="query-progress"
              role="status"
            >
              <div
                className="query-spinner"
              />

              <div>
                <strong>
                  Loading conversation…
                </strong>

                <p>
                  Restoring stored
                  messages.
                </p>
              </div>
            </section>
          ) : null}


          {conversationActionError ? (
            <StatusBanner tone="error">
              {
                conversationActionError
              }
            </StatusBanner>
          ) : null}


          {conversationMessages
            .length > 0 ? (
            <section
              className={
                "conversation-history"
              }
              aria-label={
                "Conversation history"
              }
              aria-live="polite"
            >
              {conversationMessages
                .map(
                  (message) => (
                    <ConversationMessageCard
                      key={
                        message
                          .message_id
                      }
                      message={
                        message
                      }
                      speech={
                        speech
                      }
                    />
                  ),
                )}
            </section>
          ) : (
            <section
              className={
                "answer-empty "
                + "conversation-start"
              }
            >
              <h3>
                Start a conversation
              </h3>

              <p>
                Ask a general question
                or select documents for
                a grounded answer.
                Follow-up questions can
                use bounded conversation
                context.
              </p>
            </section>
          )}


          <form
            className="question-form"
            onSubmit={
              handleSubmit
            }
          >
            <label
              className="field"
              htmlFor="mira-question"
            >
              <span>
                Your question
              </span>

              <textarea
                id="mira-question"
                rows={7}
                maxLength={
                  MAX_QUERY_CHARACTERS
                }
                value={question}
                disabled={
                  interfaceBusy
                }
                placeholder={
                  selectedDocumentIds
                    .length > 0
                    ? (
                      "Example: What "
                      + "medications and "
                      + "follow-up "
                      + "instructions "
                      + "are listed?"
                    )
                    : (
                      "Example: What is "
                      + "the difference "
                      + "between systolic "
                      + "and diastolic "
                      + "blood pressure?"
                    )
                }
                onChange={(
                  event,
                ) => {
                  setQuestion(
                    event.target
                      .value,
                  );
                }}
              />
            </label>


            <div
              className={
                "question-form__footer"
              }
            >
              <span
                className={
                  charactersRemaining
                    < 200
                    ? (
                      "character-count "
                      + "character-count--warning"
                    )
                    : "character-count"
                }
              >
                {charactersRemaining}
                {" characters remaining"}
              </span>


              <div
                className={
                  "question-actions"
                }
              >
                <VoiceInputButton
                  disabled={
                    interfaceBusy
                  }
                  onTranscript={
                    handleVoiceTranscript
                  }
                  onListeningChange={
                    setVoiceListening
                  }
                />
                {queryMutation
                  .isPending ? (
                  <button
                    className={
                      "button "
                      + "button--secondary"
                    }
                    type="button"
                    onClick={
                      cancelRequest
                    }
                  >
                    Cancel
                  </button>
                ) : null}


                <button
                  className={
                    "button "
                    + "button--primary"
                  }
                  type="submit"
                  disabled={
                    !trimmedQuestion
                    || interfaceBusy
                    || voiceListening
                  }
                >
                  {queryMutation
                    .isPending
                    ? "Asking MIRA…"
                    : "Ask MIRA"}
                </button>
              </div>
            </div>
          </form>


          {queryMutation
            .isPending ? (
            <section
              className="query-progress"
              role="status"
              aria-live="polite"
            >
              <div
                className="query-spinner"
              />

              <div>
                <strong>
                  {elapsedLabel(
                    elapsedSeconds,
                  )}
                </strong>

                <p>
                  Elapsed time:
                  {" "}
                  {elapsedSeconds}
                  {" seconds"}
                </p>
              </div>
            </section>
          ) : null}


          {queryErrorMessage ? (
            <StatusBanner tone="error">
              {queryErrorMessage}
            </StatusBanner>
          ) : null}


          {latestResult ? (
            <section
              className={
                "latest-response-meta"
              }
            >
              <header
                className={
                  "answer-panel__header"
                }
              >
                <div>
                  <p className="eyebrow">
                    Latest response
                  </p>

                  <h3>
                    {routeLabel(
                      latestResult
                        .route,
                    )}
                  </h3>
                </div>

                <span
                  className="route-badge"
                >
                  {
                    latestResult
                      .route
                  }
                </span>
              </header>


              <div
                className={
                  "answer-summary"
                }
              >
                <span>
                  {
                    latestResult
                      .selected_document_count
                  }
                  {" document"}
                  {latestResult
                    .selected_document_count
                    === 1
                    ? ""
                    : "s"}
                  {" used"}
                </span>

                <span>
                  {
                    latestResult
                      .sources.length
                  }
                  {" source"}
                  {latestResult
                    .sources.length
                    === 1
                    ? ""
                    : "s"}
                </span>
              </div>


              {latestResult
                .sources.length > 0 ? (
                <section
                  className={
                    "sources-section"
                  }
                >
                  <div>
                    <p
                      className="eyebrow"
                    >
                      Supporting context
                    </p>

                    <h4>
                      Sources
                    </h4>
                  </div>

                  <div
                    className="source-list"
                  >
                    {latestResult
                      .sources
                      .map(
                        (
                          source,
                          index,
                        ) => (
                          <SourceCard
                            key={
                              String(
                                source
                                  .chunk_id
                                ?? index,
                              )
                            }
                            source={
                              source
                            }
                            index={
                              index
                            }
                          />
                        ),
                      )}
                  </div>
                </section>
              ) : null}
            </section>
          ) : null}
        </main>
      </div>


      <section className="safety-panel">
        <div>
          <p className="eyebrow">
            Medical safety
          </p>

          <h3>
            Educational support only
          </h3>
        </div>

        <p>
          MIRA does not diagnose,
          prescribe, or replace
          professional medical judgment.
          Document-grounded answers are
          limited to the uploaded text
          and should be reviewed with a
          licensed healthcare
          professional.
        </p>
      </section>
    </section>
  );
}