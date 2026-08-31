type MockSpeechUtterance = {
  text: string;
  lang: string;
  rate: number;
  pitch: number;
  volume: number;
  onstart:
    | (() => void)
    | null;
  onend:
    | (() => void)
    | null;
  onerror:
    | (() => void)
    | null;
};


type SpeechMockState = {
  utterances:
    MockSpeechUtterance[];
  cancelCount: number;
  pauseCount: number;
  resumeCount: number;
};


const password =
  "SyntheticTest!2026";


function createSpeechMockState():
SpeechMockState {
  return {
    utterances: [],
    cancelCount: 0,
    pauseCount: 0,
    resumeCount: 0,
  };
}


let speechState =
  createSpeechMockState();


function uniqueEmail(
  prefix: string,
): string {
  return (
    `${prefix}.${Date.now()}.`
    + `${Cypress._.random(
      1000,
      9999,
    )}`
    + "@example.com"
  );
}


function installSpeechSynthesisMock(
  win: Window,
): void {
  class MockUtterance
    implements MockSpeechUtterance {
    text: string;

    lang = "";
    rate = 1;
    pitch = 1;
    volume = 1;

    onstart:
      | (() => void)
      | null = null;

    onend:
      | (() => void)
      | null = null;

    onerror:
      | (() => void)
      | null = null;


    constructor(
      text: string,
    ) {
      this.text = text;
    }
  }


  Object.defineProperty(
    win,
    "SpeechSynthesisUtterance",
    {
      configurable: true,
      writable: true,
      value:
        MockUtterance,
    },
  );


  Object.defineProperty(
    win,
    "speechSynthesis",
    {
      configurable: true,
      writable: true,
      value: {
        speak(
          utterance:
            MockSpeechUtterance,
        ) {
          speechState
            .utterances
            .push(
              utterance,
            );

          utterance
            .onstart?.();
        },

        cancel() {
          speechState
            .cancelCount += 1;
        },

        pause() {
          speechState
            .pauseCount += 1;
        },

        resume() {
          speechState
            .resumeCount += 1;
        },

        get speaking() {
          return false;
        },

        get pending() {
          return false;
        },

        get paused() {
          return false;
        },

        getVoices() {
          return [];
        },
      },
    },
  );
}


function registerUser(
  email: string,
): void {
  cy.intercept(
    "POST",
    "**/auth/register",
  ).as(
    "registerAccount",
  );


  cy.visit(
    "/register",
  );


  cy.get(
    "#register-email",
  )
    .should(
      "be.visible",
    )
    .clear()
    .type(
      email,
      {
        delay: 0,
      },
    );


  cy.get(
    "#register-password",
  )
    .should(
      "be.visible",
    )
    .clear()
    .type(
      password,
      {
        delay: 0,
        log: false,
      },
    );


  cy.get(
    "#confirm-password",
  )
    .should(
      "be.visible",
    )
    .clear()
    .type(
      password,
      {
        delay: 0,
        log: false,
      },
    );


  cy.contains(
    "button",
    "Create account",
  )
    .should(
      "be.enabled",
    )
    .click();

        /*
    * Wait for the frontend to finish its
    * post-registration authentication flow
    * before navigating elsewhere.
    */
    cy.contains(
    "Backend-connected workspace",
    {
        timeout: 30_000,
    },
    ).should(
    "be.visible",
    );
  cy.wait(
    "@registerAccount",
    {
      timeout: 30_000,
    },
  )
    .its(
      "response.statusCode",
    )
    .should(
      "be.oneOf",
      [
        200,
        201,
      ],
    );
}


function installConversationRoutes():
void {
  cy.intercept(
    "GET",
    "**/conversations/tts-conversation-1",
    {
      statusCode: 200,

      body: {
        conversation_id:
          "tts-conversation-1",

        title:
          "TTS test conversation",

        created_at:
          "2026-08-30T18:00:00Z",

        updated_at:
          "2026-08-30T18:00:01Z",

        messages: [
          {
            message_id:
              "tts-user-1",

            role:
              "user",

            content:
              "What does this result mean?",

            route:
              null,

            document_ids:
              [],

            sources:
              [],

            safety_category:
              null,

            created_at:
              "2026-08-30T18:00:00Z",
          },

          {
            message_id:
              "tts-assistant-1",

            role:
              "assistant",

            content:
              (
                "**Hemoglobin A1c** is "
                + "a blood test used to "
                + "estimate average blood "
                + "glucose over time. "
                + "[Source 1]"
              ),

            route:
              "rag",

            document_ids: [
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
                  "Synthetic source text.",
              },
            ],

            safety_category:
              null,

            created_at:
              "2026-08-30T18:00:01Z",
          },
        ],
      },
    },
  ).as(
    "firstConversation",
  );


  cy.intercept(
    "GET",
    "**/conversations/tts-conversation-2",
    {
      statusCode: 200,

      body: {
        conversation_id:
          "tts-conversation-2",

        title:
          "Second TTS conversation",

        created_at:
          "2026-08-30T18:05:00Z",

        updated_at:
          "2026-08-30T18:05:01Z",

        messages: [
          {
            message_id:
              "tts-user-2",

            role:
              "user",

            content:
              "What is systolic pressure?",

            route:
              null,

            document_ids:
              [],

            sources:
              [],

            safety_category:
              null,

            created_at:
              "2026-08-30T18:05:00Z",
          },

          {
            message_id:
              "tts-assistant-2",

            role:
              "assistant",

            content:
              (
                "Systolic pressure is "
                + "the pressure measured "
                + "when the heart contracts."
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
              "2026-08-30T18:05:01Z",
          },
        ],
      },
    },
  ).as(
    "secondConversation",
  );
}

function openAskMira():
void {
  speechState =
    createSpeechMockState();


  /*
   * Install the native browser mock before
   * React evaluates speech support.
   */
  cy.visit(
    "/ask",
    {
      onBeforeLoad(
        win,
      ) {
        installSpeechSynthesisMock(
          win,
        );
      },
    },
  );


  /*
   * First prove that the normal
   * authenticated MIRA workspace loaded.
   */


  cy.contains(
    "Conversations",
    {
      timeout: 30_000,
    },
  ).should(
    "be.visible",
  );


  /*
   * After the authenticated workspace
   * exists, install the deterministic
   * conversation responses used by TTS.
   */
  installConversationRoutes();


  /*
   * Request the deterministic conversation
   * directly through the application's
   * existing conversation-selection flow.
   *
   * We add it to the list client-side by
   * intercepting the next list refresh.
   */
  cy.intercept(
    "GET",
    "**/conversations",
    {
      statusCode: 200,

      body: {
        conversations: [
          {
            conversation_id:
              "tts-conversation-1",

            title:
              "TTS test conversation",

            message_count:
              2,

            created_at:
              "2026-08-30T18:00:00Z",

            updated_at:
              "2026-08-30T18:00:01Z",
          },

          {
            conversation_id:
              "tts-conversation-2",

            title:
              "Second TTS conversation",

            message_count:
              2,

            created_at:
              "2026-08-30T18:05:00Z",

            updated_at:
              "2026-08-30T18:05:01Z",
          },
        ],
      },
    },
  ).as(
    "ttsConversationList",
  );


  /*
   * Force React Query to fetch the newly
   * intercepted list by reloading /ask.
   *
   * The speech mock must be installed again
   * because this is a new document load.
   */
  cy.visit(
    "/ask",
    {
      onBeforeLoad(
        win,
      ) {
        installSpeechSynthesisMock(
          win,
        );
      },
    },
  );


  cy.wait(
    "@ttsConversationList",
    {
      timeout: 30_000,
    },
  );


  cy.contains(
    "TTS test conversation",
    {
      timeout: 30_000,
    },
  )
    .should(
      "be.visible",
    )
    .click();


  cy.wait(
    "@firstConversation",
    {
      timeout: 30_000,
    },
  );


  cy.contains(
    (
      "**Hemoglobin A1c** is "
      + "a blood test used to "
      + "estimate average blood "
      + "glucose over time. "
      + "[Source 1]"
    ),
    {
      timeout: 30_000,
    },
  ).should(
    "be.visible",
  );
}


describe(
  "MIRA text-to-speech",
  () => {
    beforeEach(() => {
      registerUser(
        uniqueEmail(
          "mira.tts",
        ),
      );

      openAskMira();
    });


    it(
      (
        "speaks only cleaned assistant "
        + "answer text"
      ),
      () => {
        /*
         * User messages must never expose
         * assistant TTS controls.
         */
        cy.get(
          '[data-testid="conversation-message-user"]',
        )
          .find(
            ".assistant-speech-controls",
          )
          .should(
            "not.exist",
          );


        cy.get(
          '[data-testid="conversation-message-assistant"]',
        )
          .contains(
            "button",
            "Listen",
          )
          .click();


        cy.then(
          () => {
            expect(
              speechState
                .utterances,
            ).to.have.length(
              1,
            );

            expect(
              speechState
                .utterances[0]
                .text,
            ).to.equal(
              (
                "Hemoglobin A1c is "
                + "a blood test used to "
                + "estimate average blood "
                + "glucose over time."
              ),
            );

            expect(
              speechState
                .utterances[0]
                .text,
            ).not.to.contain(
              "Source 1",
            );

            expect(
              speechState
                .utterances[0]
                .text,
            ).not.to.contain(
              "*",
            );
          },
        );
      },
    );


    it(
      (
        "pauses resumes stops "
        + "and replays a response"
      ),
      () => {
        cy.get(
          '[data-testid="conversation-message-assistant"]',
        )
          .contains(
            "button",
            "Listen",
          )
          .click();


        cy.contains(
          "button",
          "Pause",
        ).click();


        cy.then(
          () => {
            expect(
              speechState
                .pauseCount,
            ).to.equal(
              1,
            );
          },
        );


        cy.contains(
          "button",
          "Resume",
        ).click();


        cy.then(
          () => {
            expect(
              speechState
                .resumeCount,
            ).to.equal(
              1,
            );
          },
        );


        /*
         * Simulate the browser finishing
         * the utterance naturally.
         */
        cy.then(
          () => {
            speechState
              .utterances[0]
              .onend?.();
          },
        );


        cy.contains(
          "button",
          "Replay",
        )
          .should(
            "be.visible",
          )
          .click();


        cy.then(
          () => {
            expect(
              speechState
                .utterances,
            ).to.have.length(
              2,
            );
          },
        );


        const cancelCountBeforeStop =
          () => (
            speechState
              .cancelCount
          );


        cy.then(
          () => {
            cy.wrap(
              cancelCountBeforeStop(),
            ).as(
              "cancelBeforeStop",
            );
          },
        );


        cy.contains(
          "button",
          "Stop",
        ).click();


        cy.get<number>(
          "@cancelBeforeStop",
        ).then(
          (
            previousCount,
          ) => {
            expect(
              speechState
                .cancelCount,
            ).to.be.greaterThan(
              previousCount,
            );
          },
        );
      },
    );


    it(
      (
        "cancels playback when "
        + "starting a new conversation"
      ),
      () => {
        cy.contains(
          "button",
          "Listen",
        ).click();


        cy.then(
          () => {
            const before =
              speechState
                .cancelCount;


            cy.contains(
              "button",
              "Start new",
            ).click();


            cy.then(
              () => {
                expect(
                  speechState
                    .cancelCount,
                ).to.be.greaterThan(
                  before,
                );
              },
            );
          },
        );


        cy.contains(
          "Start a conversation",
        ).should(
          "be.visible",
        );
      },
    );


    it(
      (
        "cancels current playback "
        + "when switching conversations"
      ),
      () => {
        cy.contains(
          "button",
          "Listen",
        ).click();


        cy.then(
          () => {
            const before =
              speechState
                .cancelCount;


            cy.contains(
              "Second TTS conversation",
            ).click();


            cy.wait(
              "@secondConversation",
            );


            cy.then(
              () => {
                expect(
                  speechState
                    .cancelCount,
                ).to.be.greaterThan(
                  before,
                );
              },
            );
          },
        );


        cy.contains(
          (
            "Systolic pressure is "
            + "the pressure measured "
            + "when the heart contracts."
          ),
        ).should(
          "be.visible",
        );


        cy.contains(
          "button",
          "Listen",
        ).should(
          "be.visible",
        );
      },
    );
  },
);
