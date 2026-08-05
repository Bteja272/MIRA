import {
  describe,
  expect,
  it,
  vi,
} from "vitest";

import {
  clearAccessToken,
  getAccessToken,
  getTokenExpirationTime,
  isAccessTokenExpired,
  setAccessToken,
} from "./tokenStorage";

function createJwt(
  expirationSeconds: number,
): string {
  const encode = (
    value: unknown,
  ): string =>
    btoa(
      JSON.stringify(value),
    )
      .replace(/\+/g, "-")
      .replace(/\//g, "_")
      .replace(/=+$/, "");

  return [
    encode({
      alg: "none",
      typ: "JWT",
    }),
    encode({
      exp: expirationSeconds,
    }),
    "signature",
  ].join(".");
}

describe(
  "tokenStorage",
  () => {
    it(
      "stores and clears the access token",
      () => {
        setAccessToken("token-value");

        expect(
          getAccessToken(),
        ).toBe("token-value");

        clearAccessToken();

        expect(
          getAccessToken(),
        ).toBeNull();
      },
    );

    it(
      "reads the JWT expiration time",
      () => {
        const token =
          createJwt(1_800_000_000);

        expect(
          getTokenExpirationTime(token),
        ).toBe(1_800_000_000_000);
      },
    );

    it(
      "detects an expired JWT",
      () => {
        vi.useFakeTimers();

        vi.setSystemTime(
          new Date(
            "2026-08-05T18:00:00Z",
          ),
        );

        const nowSeconds =
          Math.floor(
            Date.now() / 1000,
          );

        expect(
          isAccessTokenExpired(
            createJwt(
              nowSeconds - 60,
            ),
          ),
        ).toBe(true);

        expect(
          isAccessTokenExpired(
            createJwt(
              nowSeconds + 600,
            ),
          ),
        ).toBe(false);

        vi.useRealTimers();
      },
    );

    it(
      "treats non-JWT tokens as having no known expiration",
      () => {
        expect(
          getTokenExpirationTime(
            "not-a-jwt",
          ),
        ).toBeNull();

        expect(
          isAccessTokenExpired(
            "not-a-jwt",
          ),
        ).toBe(false);
      },
    );
  },
);