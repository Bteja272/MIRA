import {
  createBrowserRouter,
} from "react-router";

import {
  ProtectedRoute,
} from "./auth/ProtectedRoute";
import {
  RouteAccessibility,
} from "./components/RouteAccessibility";
import {
  AppShell,
} from "./layout/AppShell";
import {
  AskMiraPage,
} from "./pages/AskMiraPage";
import {
  DashboardPage,
} from "./pages/DashboardPage";
import {
  DocumentsPage,
} from "./pages/DocumentsPage";
import {
  ExtractionsPage,
} from "./pages/ExtractionsPage";
import {
  LoginPage,
} from "./pages/LoginPage";
import {
  MedicalIntelligencePage,
} from "./pages/MedicalIntelligencePage";
import {
  NotFoundPage,
} from "./pages/NotFoundPage";
import {
  RegisterPage,
} from "./pages/RegisterPage";


export const router =
  createBrowserRouter([
    {
      element: (
        <RouteAccessibility />
      ),
      children: [
        {
          element: (
            <ProtectedRoute />
          ),
          children: [
            {
              element: (
                <AppShell />
              ),
              children: [
                {
                  index: true,
                  element: (
                    <DashboardPage />
                  ),
                },
                {
                  path: "documents",
                  element: (
                    <DocumentsPage />
                  ),
                },
                {
                  path: "ask",
                  element: (
                    <AskMiraPage />
                  ),
                },
                {
                  path: "extractions",
                  element: (
                    <ExtractionsPage />
                  ),
                },
                {
                  path: "intelligence",
                  element: (
                    <MedicalIntelligencePage />
                  ),
                },
              ],
            },
          ],
        },
        {
          path: "/login",
          element: <LoginPage />,
        },
        {
          path: "/register",
          element: <RegisterPage />,
        },
        {
          path: "*",
          element: <NotFoundPage />,
        },
      ],
    },
  ]);