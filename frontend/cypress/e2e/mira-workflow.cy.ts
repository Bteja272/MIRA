const password =
  "SyntheticTest!2026";

function uniqueEmail(
  prefix: string,
): string {
  return (
    `${prefix}.${Date.now()}.`
    + `${Cypress._.random(1000, 9999)}`
    + "@example.com"
  );
}

function clickNavigationLink(
  path: "/documents" | "/ask" | "/extractions",
): void {
  cy.get(
    `a[href="${path}"]:visible`,
  )
    .first()
    .should("be.visible")
    .click();
}

function registerUser(
  email: string,
): void {
  cy.visit("/register");

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

  cy.contains(
    "Backend-connected workspace",
    {
      timeout: 30_000,
    },
  ).should("be.visible");
}

function uploadSyntheticDocument():
  void {
  clickNavigationLink(
    "/documents",
  );

  cy.intercept(
    "POST",
    "**/ingest",
  ).as("ingestDocument");

  cy.get(
    "#medical-document",
  )
    .should("exist")
    .selectFile(
      "cypress/fixtures/synthetic_discharge_summary.txt",
      {
        force: true,
      },
    );

  cy.contains(
    "button",
    "Upload document",
  )
    .should("be.enabled")
    .click();

  cy.wait(
    "@ingestDocument",
    {
      timeout: 180_000,
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
    "synthetic_discharge_summary.txt",
    {
      timeout: 30_000,
    },
  ).should("be.visible");
}

function runOptionalExtraction():
  void {
  const configuredValue =
    Cypress.expose(
      "runExtraction",
    );

  const shouldRun =
    configuredValue === true
    || configuredValue === "true";

  if (!shouldRun) {
    return;
  }

  clickNavigationLink(
    "/extractions",
  );

  cy.get(
    "#extraction-document",
  )
    .should("be.enabled")
    .select(
      "synthetic_discharge_summary.txt",
    );

  cy.intercept(
    "POST",
    "**/documents/*/extract",
  ).as(
    "generateExtraction",
  );

  cy.contains(
    "button",
    "Generate extraction",
  )
    .should("be.enabled")
    .click();

  cy.wait(
    "@generateExtraction",
    {
      timeout: 420_000,
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
    "Persisted extraction",
    {
      timeout: 30_000,
    },
  ).should("be.visible");

  cy.contains(
    "Lisinopril",
  ).should("be.visible");

  cy.contains(
    "button",
    "Delete extraction",
  )
    .filter(":visible")
    .first()
    .click();

  cy.get(
    "dialog[open]",
  ).should(
    "be.visible",
  );

  cy.get(
    "dialog[open]",
  )
    .contains(
      "button",
      "Delete extraction",
    )
    .click();

  cy.contains(
    "No stored extraction",
    {
      timeout: 30_000,
    },
  ).should("be.visible");
}

describe(
  "MIRA end-to-end workflow",
  () => {
    it(
      "registers, uploads, asks a grounded question, and deletes the document",
      () => {
        const email =
          uniqueEmail(
            "mira.e2e",
          );

        registerUser(email);
        uploadSyntheticDocument();

        clickNavigationLink(
          "/ask",
        );

        cy.contains(
          "label",
          "synthetic_discharge_summary.txt",
        )
          .find(
            'input[type="checkbox"]',
          )
          .check();

        cy.get("textarea")
          .should("be.visible")
          .clear()
          .type(
            "What medications and follow-up instructions are listed?",
            {
              delay: 0,
            },
          );

        cy.intercept(
          "POST",
          "**/query",
        ).as("queryMira");

        cy.contains(
          "button",
          "Ask MIRA",
        )
          .should("be.enabled")
          .click();

        cy.wait(
          "@queryMira",
          {
            timeout: 300_000,
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
          "Document-grounded",
          {
            timeout: 30_000,
          },
        ).should("be.visible");

        cy.contains(
          "Lisinopril",
        ).should("be.visible");

        runOptionalExtraction();

        clickNavigationLink(
          "/documents",
        );

        cy.contains(
          "article",
          "synthetic_discharge_summary.txt",
        )
          .contains(
            "button",
            "Delete",
          )
          .click();

        cy.get(
          "dialog[open]",
        ).should(
          "be.visible",
        );

        cy.get(
          "dialog[open]",
        )
          .contains(
            "button",
            "Delete permanently",
          )
          .click();

        cy.contains(
          "No documents yet",
          {
            timeout: 30_000,
          },
        ).should("be.visible");

        cy.contains(
          "button",
          "Log out",
        ).click();

        cy.contains(
          "h2",
          "Log in",
        ).should("be.visible");
      },
    );

    it(
      "keeps documents isolated between accounts",
      () => {
        const userA =
          uniqueEmail(
            "mira.usera",
          );

        const userB =
          uniqueEmail(
            "mira.userb",
          );

        registerUser(userA);
        uploadSyntheticDocument();

        cy.contains(
          "button",
          "Log out",
        ).click();

        cy.contains(
          "a",
          "Create one",
        )
          .should("be.visible")
          .click();

        cy.get(
          "#register-email",
        )
          .should("be.visible")
          .clear()
          .type(
            userB,
            {
              delay: 0,
            },
          );

        cy.get(
          "#register-password",
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

        cy.contains(
          "Backend-connected workspace",
          {
            timeout: 30_000,
          },
        ).should("be.visible");

        clickNavigationLink(
          "/documents",
        );

        cy.contains(
          "No documents yet",
          {
            timeout: 30_000,
          },
        ).should("be.visible");

        cy.contains(
          "synthetic_discharge_summary.txt",
        ).should("not.exist");
      },
    );
  },
);