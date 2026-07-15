import { Outlet, Navigate, useLocation } from "react-router-dom";
import { Sidebar } from "@/components/shared/sidebar";
import { Topbar } from "@/components/shared/topbar";
import { useAuth } from "@/contexts/auth-context";

const TITLES: Record<string, { title: string; subtitle?: string }> = {
  "/dashboard": { title: "Dashboard", subtitle: "Operational overview" },
  "/live-session": { title: "Live Behavioral Session", subtitle: "Real-time observation" },
  "/trust-dna": { title: "Trust DNA", subtitle: "Six-dimension behavioral profile" },
  "/evidence": { title: "Evidence Feed", subtitle: "Explainable behavioral findings" },
  "/timeline": { title: "Behavior Timeline", subtitle: "Full session history" },
  "/recommendations": { title: "Recommendations", subtitle: "Human decision support" },
  "/reports": { title: "Session Report", subtitle: "Executive decision summary" },
  "/privacy": { title: "Privacy Center", subtitle: "Privacy by design, always visible" },
  "/settings": { title: "Settings", subtitle: "Workspace preferences" },
};

export function DashboardLayout() {
  const { isAuthenticated } = useAuth();
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  const meta = TITLES[location.pathname] ?? { title: "MAAT" };

  return (
    <div className="flex min-h-screen bg-[#fbfaf7]">
      <Sidebar />
      <div className="flex min-h-screen flex-1 flex-col">
        <Topbar title={meta.title} subtitle={meta.subtitle} />
        <main className="flex-1 px-6 py-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
