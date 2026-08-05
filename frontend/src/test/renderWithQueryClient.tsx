import {
  QueryClient,
  QueryClientProvider,
} from "@tanstack/react-query";
import {
  render,
  type RenderOptions,
} from "@testing-library/react";
import type {
  PropsWithChildren,
  ReactElement,
} from "react";
import {
  MemoryRouter,
} from "react-router";

export function createTestQueryClient():
  QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  });
}

interface RenderWithQueryClientOptions
  extends Omit<
    RenderOptions,
    "wrapper"
  > {
  route?: string;
}

export function renderWithQueryClient(
  ui: ReactElement,
  {
    route = "/",
    ...options
  }: RenderWithQueryClientOptions = {},
) {
  const queryClient =
    createTestQueryClient();

  function Wrapper({
    children,
  }: PropsWithChildren) {
    return (
      <MemoryRouter
        initialEntries={[
          route,
        ]}
      >
        <QueryClientProvider
          client={queryClient}
        >
          {children}
        </QueryClientProvider>
      </MemoryRouter>
    );
  }

  return {
    queryClient,
    ...render(
      ui,
      {
        wrapper: Wrapper,
        ...options,
      },
    ),
  };
}