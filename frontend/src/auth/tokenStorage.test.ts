import {
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";

import {
  AUTH_UNAUTHORIZED_EVENT,
  getCsrfToken,
  notifyUnauthorized,
} from "./tokenStorage";


describe(
  "tokenStorage",
  () => {
    beforeEach(
      () => {
        document.cookie =
          "mira_csrf=; "
          + "expires=Thu, 01 Jan 1970 "
          + "00:00:00 GMT; path=/";
      },
    );

    it(
      "reads the CSRF token from cookies",
      () => {
        document.cookie =
          "mira_csrf=test-csrf-token; "
          + "path=/";

        expect(
          getCsrfToken(),
        ).toBe(
          "test-csrf-token",
        );
      },
    );

    it(
      "decodes an encoded CSRF token",
      () => {
        document.cookie =
          "mira_csrf="
          + encodeURIComponent(
            "token/value+example",
          )
          + "; path=/";

        expect(
          getCsrfToken(),
        ).toBe(
          "token/value+example",
        );
      },
    );

    it(
      "returns null when CSRF cookie is absent",
      () => {
        expect(
          getCsrfToken(),
        ).toBeNull();
      },
    );

    it(
      "ignores unrelated cookies",
      () => {
        document.cookie =
          "other_cookie=value; "
          + "path=/";

        expect(
          getCsrfToken(),
        ).toBeNull();
      },
    );

    it(
      "dispatches the unauthorized event",
      () => {
        const listener =
          vi.fn();

        window.addEventListener(
          AUTH_UNAUTHORIZED_EVENT,
          listener,
        );

        notifyUnauthorized(
          "unauthorized",
        );

        expect(
          listener,
        ).toHaveBeenCalledTimes(
          1,
        );

        const event = (
          listener.mock.calls[0][0]
        ) as CustomEvent;

        expect(
          event.detail,
        ).toBe(
          "unauthorized",
        );

        window.removeEventListener(
          AUTH_UNAUTHORIZED_EVENT,
          listener,
        );
      },
    );

    it(
      "dispatches the expired reason",
      () => {
        const listener =
          vi.fn();

        window.addEventListener(
          AUTH_UNAUTHORIZED_EVENT,
          listener,
        );

        notifyUnauthorized(
          "expired",
        );

        expect(
          listener,
        ).toHaveBeenCalledTimes(
          1,
        );

        const event = (
          listener.mock.calls[0][0]
        ) as CustomEvent;

        expect(
          event.detail,
        ).toBe(
          "expired",
        );

        window.removeEventListener(
          AUTH_UNAUTHORIZED_EVENT,
          listener,
        );
      },
    );
  },
);