import {
  fireEvent,
  screen,
  within,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import {
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";



import {
  deleteConversation,
  getConversation,
  getConversations,
} from "../api/conversations";
import {
  getDocuments,
} from "../api/documents";
import {
  queryMira,
} from "../api/query";
import {
  renderWithQueryClient,
} from "../test/renderWithQueryClient";
import {
  AskMiraPage,
} from "./AskMiraPage";


const speechMocks = vi.hoisted(
  () => ({
    speak: vi.fn(),
    pause: vi.fn(),
    resume: vi.fn(),
    stop: vi.fn(),
    replay: vi.fn(),
  }),
);


vi.mock(
  "../hooks/useSpeechSynthesis",
  () => ({
    useSpeechSynthesis: () => ({
      supported: true,
      state: "idle",
      activeMessageId: null,
      lastSpokenMessageId: null,
      error: null,
      speak: speechMocks.speak,
      pause: speechMocks.pause,
      resume: speechMocks.resume,
      stop: speechMocks.stop,
      replay: speechMocks.replay,
    }),
  }),
);


vi.mock(
  "../api/documents",
  () => ({
    getDocuments: vi.fn(),
  }),
);


vi.mock(
  "../api/query",
  () => ({
    queryMira: vi.fn(),
  }),
);


vi.mock(
  "../api/conversations",
  () => ({
    getConversations: vi.fn(),
    getConversation: vi.fn(),
    deleteConversation: vi.fn(),
  }),
);


vi.mock(
  "../components/VoiceInputButton",
  () => ({
    VoiceInputButton: ({
      disabled,
      onTranscript,
      onListeningChange,
    }: {
      disabled?: boolean;

      onTranscript: (
        transcript: string,
      ) => void;

      onListeningChange?: (
        listening: boolean,
      ) => void;
    }) => (
      <div>
        <button
          type="button"
          disabled={disabled}
          onClick={() => {
            onTranscript(
              "What is hemoglobin A1c?",
            );
          }}
        >
          Mock voice transcript
        </button>

        <button
          type="button"
          onClick={() => {
            onListeningChange?.(
              true,
            );
          }}
        >
          Mock voice start
        </button>

        <button
          type="button"
          onClick={() => {
            onListeningChange?.(
              false,
            );
          }}
        >
          Mock voice stop
        </button>
      </div>
    ),
  }),
);


const mockedGetDocuments =
  vi.mocked(
    getDocuments,
  );


const mockedQueryMira =
  vi.mocked(
    queryMira,
  );


const mockedGetConversations =
  vi.mocked(
    getConversations,
  );


const mockedGetConversation =
  vi.mocked(
    getConversation,
  );


const mockedDeleteConversation =
  vi.mocked(
    deleteConversation,
  );


describe(
  "AskMiraPage",
  () => {
    beforeEach(() => {
      vi.clearAllMocks();

      mockedGetDocuments
        .mockResolvedValue({
          documents: [
            {
              document_id:
                "doc-1",
              filename:
                "synthetic.txt",
              document_type:
                "discharge_summary",
              file_size_bytes:
                200,
              chunk_count:
                2,
              uploaded_at:
                "2026-08-05T18:00:00Z",
            },
          ],
          count: 1,
        });


      mockedGetConversations
        .mockResolvedValue({
          conversations: [],
        });


      mockedDeleteConversation
        .mockResolvedValue(
          undefined,
        );
    });


    it(
      (
        "places a voice transcript in "
        + "the question field without "
        + "submitting automatically"
      ),
      async () => {
        const user =
          userEvent.setup();


        renderWithQueryClient(
          <AskMiraPage />,
        );


        await screen.findByText(
          "synthetic.txt",
        );


        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "Mock voice transcript",
            },
          ),
        );


        expect(
          screen.getByLabelText(
            "Your question",
          ),
        ).toHaveValue(
          "What is hemoglobin A1c?",
        );


        expect(
          mockedQueryMira,
        ).not.toHaveBeenCalled();
      },
    );


    it(
      (
        "appends recognized speech to "
        + "existing typed text"
      ),
      async () => {
        const user =
          userEvent.setup();


        renderWithQueryClient(
          <AskMiraPage />,
        );


        await screen.findByText(
          "synthetic.txt",
        );


        const textarea =
          screen.getByLabelText(
            "Your question",
          );


        await user.type(
          textarea,
          "Please explain",
        );


        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "Mock voice transcript",
            },
          ),
        );


        expect(
          textarea,
        ).toHaveValue(
          (
            "Please explain "
            + "What is hemoglobin A1c?"
          ),
        );
      },
    );


    it(
      (
        "prevents query submission while "
        + "voice recognition is active"
      ),
      async () => {
        const user =
          userEvent.setup();


        renderWithQueryClient(
          <AskMiraPage />,
        );


        await screen.findByText(
          "synthetic.txt",
        );


        await user.type(
          screen.getByLabelText(
            "Your question",
          ),
          "What is hemoglobin?",
        );


        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "Mock voice start",
            },
          ),
        );


        expect(
          screen.getByRole(
            "button",
            {
              name:
                "Ask MIRA",
            },
          ),
        ).toBeDisabled();


        expect(
          mockedQueryMira,
        ).not.toHaveBeenCalled();


        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "Mock voice stop",
            },
          ),
        );


        expect(
          screen.getByRole(
            "button",
            {
              name:
                "Ask MIRA",
            },
          ),
        ).toBeEnabled();
      },
    );


    it(
      (
        "keeps voice input within the "
        + "question character limit"
      ),
      async () => {
        const user =
          userEvent.setup();


        renderWithQueryClient(
          <AskMiraPage />,
        );


        await screen.findByText(
          "synthetic.txt",
        );


        const textarea =
          screen.getByLabelText(
            "Your question",
          );


        const existingText =
          "a".repeat(
            3990,
          );


        /*
        * Use a change event instead of
        * user.type() here.
        *
        * Simulating 3,990 individual
        * keystrokes is unnecessarily slow
        * and can exceed Vitest's timeout.
        */
        fireEvent.change(
          textarea,
          {
            target: {
              value:
                existingText,
            },
          },
        );


        expect(
          textarea,
        ).toHaveValue(
          existingText,
        );


        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "Mock voice transcript",
            },
          ),
        );


        const expectedValue =
        (
          existingText
          + " "
          + "What is hemoglobin A1c?"
        ).slice(
          0,
          4000,
        );

        expect(
          textarea,
        ).toHaveValue(
          expectedValue,
        );


        const textareaElement =
          textarea as HTMLTextAreaElement;

        expect(
          textareaElement.value,
        ).toHaveLength(
          4000,
        );


        expect(
          mockedQueryMira,
        ).not.toHaveBeenCalled();
      },
    );
    
    it(
      (
        "submits a direct question "
        + "without document IDs"
      ),
      async () => {
        const user =
          userEvent.setup();


        mockedQueryMira
          .mockResolvedValue({
            query:
              (
                "What is systolic "
                + "blood pressure?"
              ),
            answer:
              (
                "Systolic pressure is "
                + "measured when the "
                + "heart contracts."
              ),
            route:
              "direct",
            conversation_id:
              "conversation-1",
            message_id:
              "message-2",
            document_id:
              null,
            document_ids:
              [],
            selected_document_count:
              0,
            sources:
              [],
            safety_category:
              null,
          });


        mockedGetConversation
          .mockResolvedValue({
            conversation_id:
              "conversation-1",
            title:
              (
                "What is systolic "
                + "blood pressure?"
              ),
            created_at:
              "2026-08-27T18:00:00Z",
            updated_at:
              "2026-08-27T18:00:01Z",
            messages: [
              {
                message_id:
                  "message-1",
                role:
                  "user",
                content:
                  (
                    "What is systolic "
                    + "blood pressure?"
                  ),
                route:
                  null,
                document_ids:
                  [],
                sources:
                  [],
                safety_category:
                  null,
                created_at:
                  "2026-08-27T18:00:00Z",
              },
              {
                message_id:
                  "message-2",
                role:
                  "assistant",
                content:
                  (
                    "Systolic pressure "
                    + "is measured when "
                    + "the heart "
                    + "contracts."
                  ),
                route:
                  "direct",
                document_ids:
                  [],
                sources:
                  [],
                safety_category:
                  null,
                created_at:
                  "2026-08-27T18:00:01Z",
              },
            ],
          });


        renderWithQueryClient(
          <AskMiraPage />,
        );


        await screen.findByText(
          "synthetic.txt",
        );


        await user.type(
          screen.getByLabelText(
            "Your question",
          ),
          (
            "What is systolic "
            + "blood pressure?"
          ),
        );


        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "Ask MIRA",
            },
          ),
        );


        expect(
          await screen.findByText(
            (
              "Systolic pressure is "
              + "measured when the "
              + "heart contracts."
            ),
          ),
        ).toBeInTheDocument();


        expect(
          mockedQueryMira,
        ).toHaveBeenCalledWith(
          {
            query:
              (
                "What is systolic "
                + "blood pressure?"
              ),
            document_ids:
              undefined,
            conversation_id:
              undefined,
          },
          expect.any(
            AbortSignal,
          ),
        );


        expect(
          mockedGetConversation,
        ).toHaveBeenCalledWith(
          "conversation-1",
        );


        expect(
          await screen.findByText(
            (
              "Conversation memory "
              + "enabled"
            ),
          ),
        ).toBeInTheDocument();
      },
    );


    it(
      (
        "submits a document-grounded "
        + "question and renders its "
        + "source"
      ),
      async () => {
        const user =
          userEvent.setup();


        mockedQueryMira
          .mockResolvedValue({
            query:
              (
                "What medication "
                + "is listed?"
              ),
            answer:
              (
                "Lisinopril 10 mg once "
                + "daily is listed."
              ),
            route:
              "rag",
            conversation_id:
              "conversation-2",
            message_id:
              "message-4",
            document_id:
              "doc-1",
            document_ids:
              [
                "doc-1",
              ],
            selected_document_count:
              1,
            sources: [
              {
                source_filename:
                  "synthetic.txt",
                document_id:
                  "doc-1",
                chunk_id:
                  "chunk-1",
                chunk_index:
                  0,
                text:
                  (
                    "Medication: "
                    + "Lisinopril "
                    + "10 mg once daily."
                  ),
              },
            ],
            safety_category:
              null,
          });


        mockedGetConversation
          .mockResolvedValue({
            conversation_id:
              "conversation-2",
            title:
              (
                "What medication "
                + "is listed?"
              ),
            created_at:
              "2026-08-27T18:10:00Z",
            updated_at:
              "2026-08-27T18:10:01Z",
            messages: [
              {
                message_id:
                  "message-3",
                role:
                  "user",
                content:
                  (
                    "What medication "
                    + "is listed?"
                  ),
                route:
                  null,
                document_ids:
                  [
                    "doc-1",
                  ],
                sources:
                  [],
                safety_category:
                  null,
                created_at:
                  "2026-08-27T18:10:00Z",
              },
              {
                message_id:
                  "message-4",
                role:
                  "assistant",
                content:
                  (
                    "Lisinopril 10 mg "
                    + "once daily is "
                    + "listed."
                  ),
                route:
                  "rag",
                document_ids:
                  [
                    "doc-1",
                  ],
                sources: [
                  {
                    source_filename:
                      "synthetic.txt",
                    document_id:
                      "doc-1",
                    chunk_id:
                      "chunk-1",
                    chunk_index:
                      0,
                    text:
                      (
                        "Medication: "
                        + "Lisinopril "
                        + "10 mg once "
                        + "daily."
                      ),
                  },
                ],
                safety_category:
                  null,
                created_at:
                  "2026-08-27T18:10:01Z",
              },
            ],
          });


        renderWithQueryClient(
          <AskMiraPage />,
        );


        await user.click(
          await screen.findByRole(
            "checkbox",
            {
              name:
                /synthetic\.txt/i,
            },
          ),
        );


        await user.type(
          screen.getByLabelText(
            "Your question",
          ),
          (
            "What medication "
            + "is listed?"
          ),
        );


        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "Ask MIRA",
            },
          ),
        );


        expect(
          await screen.findByText(
            (
              "Lisinopril 10 mg "
              + "once daily is "
              + "listed."
            ),
          ),
        ).toBeInTheDocument();


        expect(
          await screen.findByText(
            "Document-grounded",
          ),
        ).toBeInTheDocument();


        expect(
          screen.getAllByText(
            "synthetic.txt",
          ).length,
        ).toBeGreaterThanOrEqual(
          1,
        );


        expect(
          mockedQueryMira,
        ).toHaveBeenCalledWith(
          {
            query:
              (
                "What medication "
                + "is listed?"
              ),
            document_ids: [
              "doc-1",
            ],
            conversation_id:
              undefined,
          },
          expect.any(
            AbortSignal,
          ),
        );


        expect(
          mockedGetConversation,
        ).toHaveBeenCalledWith(
          "conversation-2",
        );
      },
    );


    it(
      (
        "loads a saved conversation "
        + "without restoring historical "
        + "document selection"
      ),
      async () => {
        const user =
          userEvent.setup();


        mockedGetConversations
          .mockResolvedValue({
            conversations: [
              {
                conversation_id:
                  "conversation-3",
                title:
                  (
                    "What medications "
                    + "are listed?"
                  ),
                message_count:
                  2,
                created_at:
                  "2026-08-27T18:20:00Z",
                updated_at:
                  "2026-08-27T18:20:01Z",
              },
            ],
          });


        mockedGetConversation
          .mockResolvedValue({
            conversation_id:
              "conversation-3",
            title:
              (
                "What medications "
                + "are listed?"
              ),
            created_at:
              "2026-08-27T18:20:00Z",
            updated_at:
              "2026-08-27T18:20:01Z",
            messages: [
              {
                message_id:
                  "message-5",
                role:
                  "user",
                content:
                  (
                    "What medications "
                    + "are listed?"
                  ),
                route:
                  null,
                document_ids: [
                  "doc-1",
                ],
                sources:
                  [],
                safety_category:
                  null,
                created_at:
                  "2026-08-27T18:20:00Z",
              },
              {
                message_id:
                  "message-6",
                role:
                  "assistant",
                content:
                  "Lisinopril is listed.",
                route:
                  "rag",
                document_ids: [
                  "doc-1",
                ],
                sources:
                  [],
                safety_category:
                  null,
                created_at:
                  "2026-08-27T18:20:01Z",
              },
            ],
          });


        renderWithQueryClient(
          <AskMiraPage />,
        );


        await user.click(
          await screen.findByRole(
            "checkbox",
            {
              name:
                /synthetic\.txt/i,
            },
          ),
        );


        expect(
          screen.getByText(
            /1 \/ 5 selected/i,
          ),
        ).toBeInTheDocument();


        const conversationTitle =
          await screen.findByText(
            "What medications are listed?",
          );

        const conversationButton =
          conversationTitle.closest(
            "button",
          );

        expect(
          conversationButton,
        ).not.toBeNull();

        await user.click(
          conversationButton!,
        );


        expect(
          await screen.findByText(
            "Lisinopril is listed.",
          ),
        ).toBeInTheDocument();


        const assistantMessage =
          screen.getByTestId(
            "conversation-message-assistant",
          );

        await user.click(
          within(
            assistantMessage,
          ).getByRole(
            "button",
            {
              name: "Listen",
            },
          ),
        );

        expect(
          speechMocks.speak,
        ).toHaveBeenCalledWith(
          "message-6",
          "Lisinopril is listed.",
        );


        expect(
          screen.getByText(
            /0 \/ 5 selected/i,
          ),
        ).toBeInTheDocument();


        expect(
          mockedGetConversation,
        ).toHaveBeenCalledWith(
          "conversation-3",
        );
      },
    );


    it(
      "deletes an owned conversation",
      async () => {
        const user =
          userEvent.setup();


        mockedGetConversations
          .mockResolvedValue({
            conversations: [
              {
                conversation_id:
                  "conversation-4",
                title:
                  "Delete this conversation",
                message_count:
                  2,
                created_at:
                  "2026-08-27T18:30:00Z",
                updated_at:
                  "2026-08-27T18:30:01Z",
              },
            ],
          });


        vi.spyOn(
          window,
          "confirm",
        ).mockReturnValue(
          true,
        );


        renderWithQueryClient(
          <AskMiraPage />,
        );


        const deleteButton =
          await screen.findByRole(
            "button",
            {
              name:
                (
                  "Delete conversation: "
                  + "Delete this conversation"
                ),
            },
          );


        await user.click(
          deleteButton,
        );


        expect(
          mockedDeleteConversation,
        ).toHaveBeenCalledWith(
          "conversation-4",
        );
      },
    );
  },
);