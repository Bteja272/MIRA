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
    .should("be.visible")
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
    .should("be.visible")
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
    .should("be.visible")
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
    .should("be.enabled")
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


function loginUser(
  email: string,
): void {
  cy.intercept(
    "POST",
    "**/auth/login",
  ).as(
    "loginAccount",
  );

  cy.visit(
    "/login",
  );

  cy.get(
    "#login-email",
  )
    .should("be.visible")
    .clear()
    .type(
      email,
      {
        delay: 0,
      },
    );

  cy.get(
    "#login-password",
  )
    .should("be.visible")
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
    "Log in",
  )
    .should("be.enabled")
    .click();

  cy.wait(
    "@loginAccount",
    {
      timeout: 30_000,
    },
  )
    .its(
      "response.statusCode",
    )
    .should(
      "eq",
      200,
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


function logout():
  void {
  cy.contains(
    "button",
    "Log out",
  )
    .should("be.visible")
    .click();

  cy.contains(
    "h2",
    "Log in",
    {
      timeout: 30_000,
    },
  ).should(
    "be.visible",
  );
}


describe(
  "MIRA conversation memory",
  () => {
    it(
      (
        "creates, resumes, isolates, "
        + "and deletes conversations"
      ),
      () => {
        const userA =
          uniqueEmail(
            "mira.conversation.a",
          );

        const userB =
          uniqueEmail(
            "mira.conversation.b",
          );

        const firstQuestion =
          (
            "What is the difference "
            + "between systolic and "
            + "diastolic blood pressure?"
          );

        const followUp =
          (
            "Can you explain that "
            + "more simply?"
          );


        // --------------------------------
        // USER A
        // --------------------------------

        registerUser(
          userA,
        );

        cy.visit(
          "/ask",
        );

        cy.contains(
          "Conversations",
          {
            timeout: 30_000,
          },
        ).should(
          "be.visible",
        );


        cy.intercept(
          "POST",
          "**/query",
        ).as(
          "firstQuery",
        );


        cy.get(
          "#mira-question",
        )
          .should("be.visible")
          .clear()
          .type(
            firstQuestion,
            {
              delay: 0,
            },
          );


        cy.contains(
          "button",
          "Ask MIRA",
        )
          .should("be.enabled")
          .click();


        cy.wait(
          "@firstQuery",
          {
            timeout: 300_000,
          },
        ).then(
          (interception) => {
            expect(
              interception.response
                ?.statusCode,
            ).to.equal(
              200,
            );

            expect(
              interception.request
                .body
                .conversation_id,
            ).to.equal(
              undefined,
            );

            const conversationId =
              interception.response
                ?.body
                .conversation_id;

            expect(
              conversationId,
            ).to.be.a(
              "string",
            );

            cy.wrap(
              conversationId,
            ).as(
              "conversationId",
            );
          },
        );


        cy.contains(
          firstQuestion,
          {
            timeout: 30_000,
          },
        ).should(
          "be.visible",
        );


        cy.get(
          '[data-testid="conversation-message-assistant"]',
          {
            timeout: 30_000,
          },
        )
          .should(
            "have.length.at.least",
            1,
          );


        // --------------------------------
        // FOLLOW-UP
        // --------------------------------

        cy.intercept(
          "POST",
          "**/query",
        ).as(
          "followUpQuery",
        );


        cy.get(
          "#mira-question",
        )
          .clear()
          .type(
            followUp,
            {
              delay: 0,
            },
          );


        cy.contains(
          "button",
          "Ask MIRA",
        )
          .should("be.enabled")
          .click();


        cy.get<string>(
          "@conversationId",
        ).then(
          (
            conversationId,
          ) => {
            cy.wait(
              "@followUpQuery",
              {
                timeout:
                  300_000,
              },
            ).then(
              (interception) => {
                expect(
                  interception.response
                    ?.statusCode,
                ).to.equal(
                  200,
                );

                expect(
                  interception.request
                    .body
                    .conversation_id,
                ).to.equal(
                  conversationId,
                );

                expect(
                  interception.response
                    ?.body
                    .conversation_id,
                ).to.equal(
                  conversationId,
                );
              },
            );
          },
        );


        cy.contains(
          followUp,
          {
            timeout: 30_000,
          },
        ).should(
          "be.visible",
        );


        cy.get(
          '[data-testid="conversation-message-user"]',
        ).should(
          "have.length",
          2,
        );


        cy.get(
          '[data-testid="conversation-message-assistant"]',
        ).should(
          "have.length",
          2,
        );


        logout();


        // --------------------------------
        // USER B
        // --------------------------------

        registerUser(
          userB,
        );

        cy.visit(
          "/ask",
        );


        cy.contains(
          firstQuestion,
        ).should(
          "not.exist",
        );


        cy.contains(
          followUp,
        ).should(
          "not.exist",
        );


        logout();


        // --------------------------------
        // USER A RETURNS
        // --------------------------------

        loginUser(
          userA,
        );

        cy.visit(
          "/ask",
        );


        cy.contains(
          firstQuestion,
          {
            timeout: 30_000,
          },
        )
          .should(
            "be.visible",
          )
          .click();


        cy.contains(
          followUp,
          {
            timeout: 30_000,
          },
        ).should(
          "be.visible",
        );


        cy.get(
          '[data-testid="conversation-message-user"]',
        ).should(
          "have.length",
          2,
        );


        cy.get(
          '[data-testid="conversation-message-assistant"]',
        ).should(
          "have.length",
          2,
        );


        // A resumed conversation must
        // not silently restore documents.
        cy.get(
          '.connection-badge',
        ).should(
          "contain.text",
          "0 / 5 selected",
        );


        // --------------------------------
        // DELETE
        // --------------------------------

        cy.on(
          "window:confirm",
          () => true,
        );


        cy.intercept(
          "DELETE",
          "**/conversations/*",
        ).as(
          "deleteConversation",
        );


        cy.contains(
          ".conversation-item--active button",
          "Delete",
        )
          .should("be.enabled")
          .click();


        cy.wait(
          "@deleteConversation",
          {
            timeout: 30_000,
          },
        )
          .its(
            "response.statusCode",
          )
          .should(
            "eq",
            204,
          );


        cy.contains(
          followUp,
        ).should(
          "not.exist",
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