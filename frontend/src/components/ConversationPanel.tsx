import type {
  ConversationSummary,
} from "../types/conversation";


interface ConversationPanelProps {
  conversations:
    ConversationSummary[];

  activeConversationId:
    string | null;

  loading: boolean;

  disabled: boolean;

  deletingConversationId:
    string | null;

  onNewConversation:
    () => void;

  onSelectConversation:
    (
      conversationId: string,
    ) => void;

  onDeleteConversation:
    (
      conversationId: string,
    ) => void;
}


function messageCountLabel(
  count: number,
): string {
  return (
    `${count} message`
    + (count === 1 ? "" : "s")
  );
}


export function ConversationPanel({
  conversations,
  activeConversationId,
  loading,
  disabled,
  deletingConversationId,
  onNewConversation,
  onSelectConversation,
  onDeleteConversation,
}: ConversationPanelProps) {
  return (
    <section
      className="conversation-panel"
      aria-label="Saved conversations"
    >
      <div
        className={
          "conversation-panel__header"
        }
      >
        <div>
          <p className="eyebrow">
            Memory
          </p>

          <h3>
            Conversations
          </h3>
        </div>

        <button
          className="text-button"
          type="button"
          disabled={disabled}
          onClick={
            onNewConversation
          }
        >
          New
        </button>
      </div>

      <p
        className={
          "conversation-panel__note"
        }
      >
        Conversation text can provide
        continuity. Document selection
        remains explicit for each query.
      </p>

      {loading ? (
        <div
          className="conversation-empty"
          role="status"
        >
          Loading conversations…
        </div>
      ) : conversations.length
        === 0 ? (
          <div
            className={
              "conversation-empty"
            }
          >
            No saved conversations yet.
          </div>
        ) : (
          <div
            className="conversation-list"
          >
            {conversations.map(
              (conversation) => {
                const isActive = (
                  activeConversationId
                  === conversation
                    .conversation_id
                );

                const isDeleting = (
                  deletingConversationId
                  === conversation
                    .conversation_id
                );

                return (
                  <article
                    key={
                      conversation
                        .conversation_id
                    }
                    className={
                      isActive
                        ? (
                          "conversation-item "
                          + "conversation-item--active"
                        )
                        : "conversation-item"
                    }
                  >
                    <button
                      className={
                        "conversation-item__open"
                      }
                      type="button"
                      disabled={
                        disabled
                        || isDeleting
                      }
                      aria-current={
                        isActive
                          ? "true"
                          : undefined
                      }
                      onClick={() => {
                        onSelectConversation(
                          conversation
                            .conversation_id,
                        );
                      }}
                    >
                      <strong>
                        {
                          conversation
                            .title
                        }
                      </strong>

                      <span>
                        {messageCountLabel(
                          conversation
                            .message_count,
                        )}
                      </span>
                    </button>

                    <button
                      className={
                        "conversation-item__delete"
                      }
                      type="button"
                      disabled={
                        disabled
                        || isDeleting
                      }
                      aria-label={
                        (
                          "Delete conversation: "
                          + conversation.title
                        )
                      }
                      onClick={() => {
                        onDeleteConversation(
                          conversation
                            .conversation_id,
                        );
                      }}
                    >
                      {isDeleting
                        ? "Deleting…"
                        : "Delete"}
                    </button>
                  </article>
                );
              },
            )}
          </div>
        )}
    </section>
  );
}