type RecognitionResult = {
  isFinal: boolean;

  0: {
    transcript: string;
  };

  length: number;
};


class MockSpeechRecognition {
  static latest:
    MockSpeechRecognition | null = null;

  static abortCount = 0;

  continuous = false;
  interimResults = false;
  lang = "en-US";

  onstart:
    | (() => void)
    | null = null;

  onend:
    | (() => void)
    | null = null;

  onresult:
    | ((event: {
      resultIndex: number;
      results:
        RecognitionResult[];
    }) => void)
    | null = null;

  onerror:
    | ((event: {
      error: string;
    }) => void)
    | null = null;


  constructor() {
    MockSpeechRecognition.latest =
      this;
  }


  start(): void {
    this.onstart?.();
  }


  stop(): void {
    this.onend?.();
  }


  abort(): void {
    MockSpeechRecognition
      .abortCount += 1;

    this.onend?.();
  }


  emitFinal(
    transcript: string,
  ): void {
    this.onresult?.({
      resultIndex: 0,

      results: [
        {
          isFinal: true,

          0: {
            transcript,
          },

          length: 1,
        },
      ],
    });
  }
}


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
};


const password =
  "SyntheticTest!2026";


function createSpeechMockState():
SpeechMockState {
  return {
    utterances: [],
    cancelCount: 0,
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


function installSpeechRecognitionMock(
  win: Window,
): void {
  Object.defineProperty(
    win,
    "SpeechRecognition",
    {
      configurable: true,
      writable: true,
      value:
        MockSpeechRecognition,
    },
  );


  Object.defineProperty(
    win,
    "webkitSpeechRecognition",
    {
      configurable: true,
      writable: true,
      value:
        MockSpeechRecognition,
    },
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

        pause() {},

        resume() {},

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


function installVoiceMocks(
  win: Window,
): void {
  installSpeechRecognitionMock(
    win,
  );

  installSpeechSynthesisMock(
    win,
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


  cy.contains(
    "Backend-connected workspace",
    {
      timeout: 30_000,
    },
  ).should(
    "be.visible",
  );
}


function installConversationRoutes():
void {
  cy.intercept(
    "GET",
    "**/conversations",
    {
      statusCode: 200,

      body: {
        conversations: [
          {
            conversation_id:
              "voice-integration-1",

            title:
              "Voice integration conversation",

            message_count:
              2,

            created_at:
              "2026-09-04T18:00:00Z",

            updated_at:
              "2026-09-04T18:00:01Z",
          },
        ],
      },
    },
  ).as(
    "voiceConversationList",
  );


  cy.intercept(
    "GET",
    "**/conversations/voice-integration-1",
    {
      statusCode: 200,

      body: {
        conversation_id:
          "voice-integration-1",

        title:
          "Voice integration conversation",

        created_at:
          "2026-09-04T18:00:00Z",

        updated_at:
          "2026-09-04T18:00:01Z",

        messages: [
          {
            message_id:
              "voice-user-1",

            role:
              "user",

            content:
              "What does hemoglobin mean?",

            route:
              null,

            document_ids: [],
            sources: [],
            safety_category:
              null,

            created_at:
              "2026-09-04T18:00:00Z",
          },

          {
            message_id:
              "voice-assistant-1",

            role:
              "assistant",

            content:
              (
                "Hemoglobin carries oxygen "
                + "in red blood cells."
              ),

            route:
              "direct",

            document_ids: [],
            sources: [],
            safety_category:
              null,

            created_at:
              "2026-09-04T18:00:01Z",
          },
        ],
      },
    },
  ).as(
    "voiceConversation",
  );
}


function openVoiceConversation():
void {
  speechState =
    createSpeechMockState();

  MockSpeechRecognition.latest =
    null;

  MockSpeechRecognition.abortCount =
    0;


  installConversationRoutes();


  cy.visit(
    "/ask",
    {
      onBeforeLoad(
        win,
      ) {
        installVoiceMocks(
          win,
        );
      },
    },
  );


  cy.wait(
    "@voiceConversationList",
    {
      timeout: 30_000,
    },
  );


  cy.contains(
    "Voice integration conversation",
    {
      timeout: 30_000,
    },
  )
    .should(
      "be.visible",
    )
    .click();


  cy.wait(
    "@voiceConversation",
    {
      timeout: 30_000,
    },
  );


  cy.contains(
    "Hemoglobin carries oxygen in red blood cells.",
    {
      timeout: 30_000,
    },
  ).should(
    "be.visible",
  );
}


describe(
  "MIRA combined voice integration",
  () => {
    beforeEach(() => {
      registerUser(
        uniqueEmail(
          "mira.voice.integration",
        ),
      );

      openVoiceConversation();
    });


    it(
      (
        "stops TTS before "
        + "starting STT"
      ),
      () => {
        cy.contains(
          "button",
          "Listen",
        ).click();


        cy.then(
          () => {
            expect(
              speechState
                .utterances,
            ).to.have.length(
              1,
            );

            const cancelBefore =
              speechState
                .cancelCount;


            cy.contains(
              "button",
              "Voice input",
            ).click();


            cy.contains(
              "button",
              "Stop listening",
            ).should(
              "be.visible",
            );


            cy.then(
              () => {
                expect(
                  speechState
                    .cancelCount,
                ).to.be.greaterThan(
                  cancelBefore,
                );
              },
            );
          },
        );
      },
    );


    it(
      (
        "aborts STT before "
        + "starting TTS"
      ),
      () => {
        cy.contains(
          "button",
          "Voice input",
        ).click();


        cy.contains(
          "button",
          "Stop listening",
        ).should(
          "be.visible",
        );


        cy.then(
          () => {
            const abortBefore =
              MockSpeechRecognition
                .abortCount;


            cy.contains(
              "button",
              "Listen",
            ).click();


            cy.then(
              () => {
                expect(
                  MockSpeechRecognition
                    .abortCount,
                ).to.be.greaterThan(
                  abortBefore,
                );

                expect(
                  speechState
                    .utterances,
                ).to.have.length(
                  1,
                );
              },
            );
          },
        );


        cy.contains(
          "button",
          "Stop listening",
        ).should(
          "not.exist",
        );


        cy.contains(
          "button",
          "Pause",
        ).should(
          "be.visible",
        );
      },
    );


    it(
      (
        "supports TTS to STT "
        + "to TTS handoff"
      ),
      () => {
        cy.contains(
          "button",
          "Listen",
        ).click();


        cy.contains(
          "button",
          "Voice input",
        ).click();


        cy.contains(
          "button",
          "Stop listening",
        ).should(
          "be.visible",
        );


        cy.window().then(
          () => {
            MockSpeechRecognition
              .latest!
              .emitFinal(
                "Explain oxygen transport.",
              );
          },
        );


        cy.get(
          "#mira-question",
        ).should(
          "have.value",
          "Explain oxygen transport.",
        );


        cy.contains(
          "button",
          "Listen",
        ).click();


        cy.contains(
          "button",
          "Stop listening",
        ).should(
          "not.exist",
        );


        cy.contains(
          "button",
          "Pause",
        ).should(
          "be.visible",
        );


        cy.then(
          () => {
            expect(
              MockSpeechRecognition
                .abortCount,
            ).to.be.greaterThan(
              0,
            );

            expect(
              speechState
                .utterances
                .length,
            ).to.be.greaterThan(
              1,
            );
          },
        );
      },
    );


    it(
      (
        "stops playback on "
        + "new conversation"
      ),
      () => {
        cy.contains(
          "button",
          "Listen",
        ).click();


        cy.then(
          () => {
            const cancelBefore =
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
                  cancelBefore,
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
  },
);
