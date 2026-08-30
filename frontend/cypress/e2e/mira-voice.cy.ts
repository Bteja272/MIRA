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
    this.onend?.();
  }


  emitInterim(
    transcript: string,
  ): void {
    this.onresult?.({
      resultIndex: 0,

      results: [
        {
          isFinal:
            false,

          0: {
            transcript,
          },

          length: 1,
        },
      ],
    });
  }


  emitFinal(
    transcript: string,
  ): void {
    this.onresult?.({
      resultIndex: 0,

      results: [
        {
          isFinal:
            true,

          0: {
            transcript,
          },

          length: 1,
        },
      ],
    });
  }


  emitError(
    error: string,
  ): void {
    this.onerror?.({
      error,
    });

    /*
     * Real browsers commonly emit
     * onend after an error.
     */
    this.onend?.();
  }
}


const password =
  "SyntheticTest!2026";


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


function openAskMira():
  void {
  MockSpeechRecognition.latest =
    null;


  /*
   * Registration has already created
   * the authenticated HttpOnly cookies.
   *
   * Visiting /ask mirrors the existing
   * green conversation E2E flow, while
   * onBeforeLoad installs the browser
   * speech mock before React initializes.
   */
  cy.visit(
    "/ask",
    {
      onBeforeLoad(
        win,
      ) {
        installSpeechRecognitionMock(
          win,
        );
      },
    },
  );


  cy.contains(
    "Conversations",
    {
      timeout: 30_000,
    },
  ).should(
    "be.visible",
  );


  cy.get(
    "#mira-question",
  ).should(
    "be.visible",
  );


  cy.contains(
    "button",
    "Voice input",
  ).should(
    "be.visible",
  );
}


describe(
  "MIRA voice input",
  () => {
    beforeEach(() => {
      MockSpeechRecognition.latest =
        null;
    });


    it(
      (
        "transcribes voice input "
        + "without automatically "
        + "submitting the query"
      ),
      () => {
        const email =
          uniqueEmail(
            "mira.voice.transcript",
          );


        registerUser(
          email,
        );


        openAskMira();


        let queryRequestCount =
          0;


        cy.intercept(
          "POST",
          "**/query",
          (request) => {
            queryRequestCount += 1;

            request.continue();
          },
        );


        cy.contains(
          "button",
          "Voice input",
        )
          .should(
            "be.enabled",
          )
          .click();


        cy.contains(
          "button",
          "Stop listening",
        ).should(
          "be.visible",
        );


        cy.window().then(
          () => {
            expect(
              MockSpeechRecognition
                .latest,
            ).not.to.equal(
              null,
            );


            MockSpeechRecognition
              .latest!
              .emitInterim(
                "What is hemoglobin",
              );
          },
        );


        cy.contains(
          (
            "Listening: "
            + "What is hemoglobin"
          ),
        ).should(
          "be.visible",
        );


        cy.window().then(
          () => {
            MockSpeechRecognition
              .latest!
              .emitFinal(
                (
                  "What is "
                  + "hemoglobin A1c?"
                ),
              );
          },
        );


        cy.get(
          "#mira-question",
        ).should(
          "have.value",
          (
            "What is "
            + "hemoglobin A1c?"
          ),
        );


        /*
         * Voice transcription must never
         * automatically call /query.
         */
        cy.then(
          () => {
            expect(
              queryRequestCount,
            ).to.equal(
              0,
            );
          },
        );


        cy.contains(
          "button",
          "Stop listening",
        ).click();


        cy.contains(
          "button",
          "Ask MIRA",
        ).should(
          "be.enabled",
        );


        cy.then(
          () => {
            expect(
              queryRequestCount,
            ).to.equal(
              0,
            );
          },
        );
      },
    );


    it(
      (
        "appends recognized speech "
        + "to existing typed text"
      ),
      () => {
        const email =
          uniqueEmail(
            "mira.voice.append",
          );


        registerUser(
          email,
        );


        openAskMira();


        cy.get(
          "#mira-question",
        )
          .clear()
          .type(
            "Please explain",
            {
              delay: 0,
            },
          );


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
            expect(
              MockSpeechRecognition
                .latest,
            ).not.to.equal(
              null,
            );


            MockSpeechRecognition
              .latest!
              .emitFinal(
                (
                  "What is "
                  + "hemoglobin A1c?"
                ),
              );
          },
        );


        cy.get(
          "#mira-question",
        ).should(
          "have.value",
          (
            "Please explain "
            + "What is "
            + "hemoglobin A1c?"
          ),
        );


        cy.contains(
          "button",
          "Stop listening",
        ).click();
      },
    );


    it(
      (
        "keeps Ask MIRA disabled "
        + "while recognition is active"
      ),
      () => {
        const email =
          uniqueEmail(
            "mira.voice.busy",
          );


        registerUser(
          email,
        );


        openAskMira();


        cy.get(
          "#mira-question",
        )
          .clear()
          .type(
            "What is hemoglobin?",
            {
              delay: 0,
            },
          );


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


        cy.contains(
          "button",
          "Ask MIRA",
        ).should(
          "be.disabled",
        );


        cy.contains(
          "button",
          "Stop listening",
        ).click();


        cy.contains(
          "button",
          "Ask MIRA",
        ).should(
          "be.enabled",
        );
      },
    );


    it(
      (
        "shows a microphone "
        + "permission error"
      ),
      () => {
        const email =
          uniqueEmail(
            "mira.voice.permission",
          );


        registerUser(
          email,
        );


        openAskMira();


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
            expect(
              MockSpeechRecognition
                .latest,
            ).not.to.equal(
              null,
            );


            MockSpeechRecognition
              .latest!
              .emitError(
                "not-allowed",
              );
          },
        );


        cy.contains(
          (
            "Microphone access "
            + "was denied."
          ),
        ).should(
          "be.visible",
        );


        cy.contains(
          "button",
          "Voice input",
        ).should(
          "be.enabled",
        );
      },
    );
  },
);