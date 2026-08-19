const password =
  "SyntheticTest!2026";

function uniqueEmail():
  string {
  return (
    "mira.security."
    + Date.now()
    + "."
    + Cypress._.random(
      1000,
      9999,
    )
    + "@example.com"
  );
}

describe(
  "MIRA browser session security",
  () => {
    it(
      "uses HttpOnly authentication cookies instead of browser token storage",
      () => {
        const email =
          uniqueEmail();

        cy.visit("/register");

        cy.get(
          "#register-email",
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
        ).click();

        cy.contains(
          "Backend-connected workspace",
          {
            timeout: 30_000,
          },
        ).should(
          "be.visible",
        );

        cy.getCookie(
          "mira_access",
        )
          .should("exist")
          .then((cookie) => {
            expect(
              cookie?.httpOnly,
            ).to.equal(true);
          });

        cy.getCookie(
          "mira_refresh",
        )
          .should("exist")
          .then((cookie) => {
            expect(
              cookie?.httpOnly,
            ).to.equal(true);
          });

        cy.getCookie(
          "mira_csrf",
        )
          .should("exist")
          .then((cookie) => {
            expect(
              cookie?.httpOnly,
            ).to.equal(false);
          });

        cy.window().then(
          (window) => {
            expect(
              window.sessionStorage
                .getItem(
                  "mira_access_token",
                ),
            ).to.equal(null);

            expect(
              window.localStorage
                .getItem(
                  "mira_access_token",
                ),
            ).to.equal(null);
          },
        );

        cy.contains(
          "button",
          "Log out",
        ).click();

        cy.contains(
          "h2",
          "Log in",
        ).should(
          "be.visible",
        );

        cy.getCookies().then(
          (cookies) => {
            cy.log(
              JSON.stringify(
                cookies.map(
                  (cookie) => ({
                    name: cookie.name,
                    path: cookie.path,
                    domain: cookie.domain,
                    httpOnly:
                      cookie.httpOnly,
                  }),
                ),
              ),
            );

            console.log(
              "COOKIES AFTER LOGOUT:",
              cookies,
            );
          },
        );

        cy.getCookie(
          "mira_access",
        ).should(
          "not.exist",
        );

        cy.getCookie(
          "mira_refresh",
        ).should(
          "not.exist",
        );
      },
    );
  },
);