import {
  defineConfig,
} from "cypress";

export default defineConfig({
  allowCypressEnv: false,

  expose: {
    runExtraction: false,
  },

  e2e: {
    baseUrl:
      process.env.CYPRESS_BASE_URL
      ?? "http://127.0.0.1:5173",

    supportFile:
      "cypress/support/e2e.ts",

    specPattern:
      "cypress/e2e/**/*.cy.{ts,tsx}",

    defaultCommandTimeout:
      15_000,

    requestTimeout:
      30_000,

    responseTimeout:
      300_000,

    video: false,

    screenshotOnRunFailure: true,
  },
});