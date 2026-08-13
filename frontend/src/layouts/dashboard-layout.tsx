import * as React from "react";
import { Outlet, Navigate, useLocation } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import { Sidebar } from "@/components/shared/sidebar";
import { Topbar } from "@/components/shared/topbar";
import { MobileNav } from "@/components/shared/mobile-nav";
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
  "/pricing": { title: "Plans", subtitle: "Choose the plan that fits your team" },
  "/settings": { title: "Settings", subtitle: "Workspace preferences" },
};

export function DashboardLayout() {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();
  const [mobileNavOpen, setMobileNavOpen] = React.useState(false);

  React.useEffect(() => {
    setMobileNavOpen(false);
  }, [location.pathname]);

  // A stored token (see api-client.ts) is validated against GET /auth/me
  // on mount — until that resolves, isAuthenticated is provisionally
  // false even for a returning, still-logged-in user. Redirecting to
  // /login during that window would bounce a valid session; wait for it.
  if (isLoading) {
    return null;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  const meta = TITLES[location.pathname] ?? { title: "MAAT" };

  return (
    <div className="flex min-h-screen bg-[#fbfaf7]">
      <Sidebar />
      <MobileNav open={mobileNavOpen} onClose={() => setMobileNavOpen(false)} />
      <div className="flex min-h-screen flex-1 flex-col">
        <Topbar title={meta.title} subtitle={meta.subtitle} onMenuClick={() => setMobileNavOpen(true)} />
        <main className="flex-1 px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
          <div className="mx-auto max-w-[1400px]">
            <AnimatePresence mode="wait">
              <motion.div
                key={location.pathname}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -6 }}
                transition={{ duration: 0.22, ease: "easeOut" }}
              >
                <Outlet />
              </motion.div>
            </AnimatePresence>
          </div>
        </main>
      </div>
    </div>
  );
}
