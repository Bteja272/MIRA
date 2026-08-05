import {
  render,
  screen,
} from "@testing-library/react";
import {
  MemoryRouter,
  Route,
  Routes,
} from "react-router";
import {
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";

import {
  ProtectedRoute,
} from "./ProtectedRoute";
import {
  useAuth,
} from "./useAuth";

vi.mock(
  "./useAuth",
  () => ({
    useAuth: vi.fn(),
  }),
);

const mockedUseAuth =
  vi.mocked(useAuth);

describe(
  "ProtectedRoute",
  () => {
    beforeEach(() => {
      mockedUseAuth.mockReset();
    });

    it(
      "renders the protected route for an authenticated user",
      () => {
        mockedUseAuth.mockReturnValue({
          user: {
            user_id: "user-1",
            email: "user@example.com",
            is_active: true,
            created_at:
              "2026-08-05T18:00:00Z",
          },
          isInitializing: false,
          isAuthenticated: true,
          sessionEndReason: null,
          login: vi.fn(),
          register: vi.fn(),
          logout: vi.fn(),
        });

        render(
          <MemoryRouter
            initialEntries={[
              "/documents",
            ]}
          >
            <Routes>
              <Route
                element={
                  <ProtectedRoute />
                }
              >
                <Route
                  path="/documents"
                  element={
                    <div>
                      Protected content
                    </div>
                  }
                />
              </Route>

              <Route
                path="/login"
                element={
                  <div>
                    Login page
                  </div>
                }
              />
            </Routes>
          </MemoryRouter>,
        );

        expect(
          screen.getByText(
            "Protected content",
          ),
        ).toBeInTheDocument();
      },
    );

    it(
      "redirects an unauthenticated user to login",
      () => {
        mockedUseAuth.mockReturnValue({
          user: null,
          isInitializing: false,
          isAuthenticated: false,
          sessionEndReason:
            "expired",
          login: vi.fn(),
          register: vi.fn(),
          logout: vi.fn(),
        });

        render(
          <MemoryRouter
            initialEntries={[
              "/documents",
            ]}
          >
            <Routes>
              <Route
                element={
                  <ProtectedRoute />
                }
              >
                <Route
                  path="/documents"
                  element={
                    <div>
                      Protected content
                    </div>
                  }
                />
              </Route>

              <Route
                path="/login"
                element={
                  <div>
                    Login page
                  </div>
                }
              />
            </Routes>
          </MemoryRouter>,
        );

        expect(
          screen.getByText(
            "Login page",
          ),
        ).toBeInTheDocument();
      },
    );

    it(
      "shows a session check while initialization is pending",
      () => {
        mockedUseAuth.mockReturnValue({
          user: null,
          isInitializing: true,
          isAuthenticated: false,
          sessionEndReason: null,
          login: vi.fn(),
          register: vi.fn(),
          logout: vi.fn(),
        });

        render(
          <MemoryRouter>
            <Routes>
              <Route
                element={
                  <ProtectedRoute />
                }
              >
                <Route
                  path="*"
                  element={
                    <div>
                      Protected content
                    </div>
                  }
                />
              </Route>
            </Routes>
          </MemoryRouter>,
        );

        expect(
          screen.getByText(
            "Checking your session…",
          ),
        ).toBeInTheDocument();
      },
    );
  },
);