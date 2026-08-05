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

function registerUser(
  email: string,
): void {
  cy.visit("/register");

  cy.findByLabelText(
    "Email",
  ).type(email);

  cy.findByLabelText(
    "Password",
  ).type(password);

  cy.findByLabelText(
    "Confirm password",
  ).type(password);

  cy.contains(
    "button",
    "Create account",
  ).click();

  cy.contains(
    "Backend-connected workspace",
    {
      timeout: 30_000,
    },
  ).should("be.visible");
}

function uploadSyntheticDocument():
  void {
  cy.contains(
    "a",
    "Documents",
  ).click();

  cy.intercept(
    "POST",
    "**/ingest",
  ).as("ingestDocument");

  cy.get(
    'input[type="file"]',
  ).selectFile(
    "cypress/fixtures/synthetic_discharge_summary.txt",
    {
      force: true,
    },
  );

  cy.contains(
    "button",
    "Upload document",
  ).click();

  cy.wait(
    "@ingestDocument",
    {
      timeout: 180_000,
    },
  ).its(
    "response.statusCode",
  ).should(
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

describe(
  "MIRA end-to-end workflow",
  () => {
    it(
      "registers, uploads, asks a grounded question, and deletes the document",
      () => {
        const email =
          uniqueEmail("mira.e2e");

        registerUser(email);
        uploadSyntheticDocument();

        cy.contains(
          "a",
          "Ask MIRA",
        ).click();

        cy.contains(
          "label",
          "synthetic_discharge_summary.txt",
        )
          .find(
            'input[type="checkbox"]',
          )
          .check();

        cy.findByLabelText(
          "Your question",
        ).type(
          "What medications and follow-up instructions are listed?",
        );

        cy.intercept(
          "POST",
          "**/query",
        ).as("queryMira");

        cy.contains(
          "button",
          "Ask MIRA",
        ).click();

        cy.wait(
          "@queryMira",
          {
            timeout: 300_000,
          },
        ).its(
          "response.statusCode",
        ).should(
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

        const runExtraction =
          Cypress.env(
            "runExtraction",
          );

        if (
          runExtraction === true
          || runExtraction === "true"
        ) {
          cy.contains(
            "a",
            "Extractions",
          ).click();

          cy.findByLabelText(
            "Select a document",
          ).select(
            "synthetic_discharge_summary.txt",
          );

          cy.intercept(
            "POST",
            "**/documents/*/extract",
          ).as("generateExtraction");

          cy.contains(
            "button",
            "Generate extraction",
          ).click();

          cy.wait(
            "@generateExtraction",
            {
              timeout: 420_000,
            },
          ).its(
            "response.statusCode",
          ).should(
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
          ).click();

          cy.get("dialog")
            .contains(
              "button",
              "Delete extraction",
            )
            .click();

          cy.contains(
            "No stored extraction",
          ).should("be.visible");
        }

        cy.contains(
          "a",
          "Documents",
        ).click();

        cy.contains(
          "article",
          "synthetic_discharge_summary.txt",
        )
          .contains(
            "button",
            "Delete",
          )
          .click();

        cy.get("dialog")
          .contains(
            "button",
            "Delete permanently",
          )
          .click();

        cy.contains(
          "No documents yet",
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
          uniqueEmail("mira.usera");

        const userB =
          uniqueEmail("mira.userb");

        registerUser(userA);
        uploadSyntheticDocument();

        cy.contains(
          "button",
          "Log out",
        ).click();

        cy.contains(
          "a",
          "Create one",
        ).click();

        cy.findByLabelText(
          "Email",
        ).type(userB);

        cy.findByLabelText(
          "Password",
        ).type(password);

        cy.findByLabelText(
          "Confirm password",
        ).type(password);

        cy.contains(
          "button",
          "Create account",
        ).click();

        cy.contains(
          "a",
          "Documents",
        ).click();

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