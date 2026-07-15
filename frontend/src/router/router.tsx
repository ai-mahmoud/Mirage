import { createBrowserRouter } from "react-router-dom";
import { DashboardLayout } from "@/layouts/dashboard-layout";
import { AuthLayout } from "@/layouts/auth-layout";
import { LandingPage } from "@/features/landing/landing-page";
import { LoginPage } from "@/features/auth/login-page";
import { DashboardPage } from "@/features/dashboard/dashboard-page";
import { LiveSessionPage } from "@/features/live-session/live-session-page";
import { TrustDnaPage } from "@/features/trust-dna/trust-dna-page";
import { EvidencePage } from "@/features/evidence/evidence-page";
import { TimelinePage } from "@/features/timeline/timeline-page";
import { RecommendationsPage } from "@/features/recommendations/recommendations-page";
import { ReportsPage } from "@/features/reports/reports-page";
import { PrivacyPage } from "@/features/privacy/privacy-page";
import { SettingsPage } from "@/features/settings/settings-page";
import { NotFoundPage } from "@/features/not-found/not-found-page";

export const router = createBrowserRouter([
  { path: "/", element: <LandingPage /> },
  {
    element: <AuthLayout />,
    children: [{ path: "/login", element: <LoginPage /> }],
  },
  {
    element: <DashboardLayout />,
    children: [
      { path: "/dashboard", element: <DashboardPage /> },
      { path: "/live-session", element: <LiveSessionPage /> },
      { path: "/trust-dna", element: <TrustDnaPage /> },
      { path: "/evidence", element: <EvidencePage /> },
      { path: "/timeline", element: <TimelinePage /> },
      { path: "/recommendations", element: <RecommendationsPage /> },
      { path: "/reports", element: <ReportsPage /> },
      { path: "/privacy", element: <PrivacyPage /> },
      { path: "/settings", element: <SettingsPage /> },
    ],
  },
  { path: "*", element: <NotFoundPage /> },
]);
