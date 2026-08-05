import "@testing-library/cypress/add-commands";

beforeEach(() => {
  cy.clearCookies();
  cy.clearLocalStorage();

  cy.window().then(
    (windowObject) => {
      windowObject
        .sessionStorage
        .clear();
    },
  );
});