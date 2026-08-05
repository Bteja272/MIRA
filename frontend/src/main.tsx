import {
  StrictMode,
} from "react";
import {
  createRoot,
} from "react-dom/client";
import {
  QueryClient,
  QueryClientProvider,
} from "@tanstack/react-query";
import {
  RouterProvider,
} from "react-router/dom";

import {
  AuthProvider,
} from "./auth/AuthProvider";
import {
  AppErrorBoundary,
} from "./components/AppErrorBoundary";
import {
  NetworkStatusBanner,
} from "./components/NetworkStatusBanner";
import {
  router,
} from "./router";
import "./styles/global.css";

const queryClient =
  new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 30_000,
        retry: (
          failureCount,
          error,
        ) => {
          if (
            error
            && typeof error === "object"
            && "status" in error
            && (
              error.status === 401
              || error.status === 403
              || error.status === 404
            )
          ) {
            return false;
          }

          return failureCount < 1;
        },
        refetchOnWindowFocus: false,
      },
      mutations: {
        retry: 0,
      },
    },
  });

const rootElement =
  document.getElementById(
    "root",
  );

if (!rootElement) {
  throw new Error(
    "The root element was not found.",
  );
}

createRoot(rootElement).render(
  <StrictMode>
    <AppErrorBoundary>
      <QueryClientProvider
        client={queryClient}
      >
        <AuthProvider>
          <NetworkStatusBanner />

          <RouterProvider
            router={router}
          />
        </AuthProvider>
      </QueryClientProvider>
    </AppErrorBoundary>
  </StrictMode>,
);