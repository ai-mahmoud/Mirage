import { NavLink } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import {
  LayoutDashboard,
  Radio,
  Dna,
  Feather,
  GitCommitHorizontal,
  ShieldCheck,
  FileText,
  Lock,
  Settings,
  X,
} from "lucide-react";
import { LogoMark, Wordmark } from "@/components/shared/logo-mark";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/live-session", label: "Live Session", icon: Radio },
  { to: "/trust-dna", label: "Trust DNA", icon: Dna },
  { to: "/evidence", label: "Evidence Feed", icon: Feather },
  { to: "/timeline", label: "Behavior Timeline", icon: GitCommitHorizontal },
  { to: "/recommendations", label: "Recommendations", icon: ShieldCheck },
  { to: "/reports", label: "Session Report", icon: FileText },
  { to: "/privacy", label: "Privacy Center", icon: Lock },
  { to: "/settings", label: "Settings", icon: Settings },
];

export function MobileNav({ open, onClose }: { open: boolean; onClose: () => void }) {
  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-40 bg-charcoal-900/40 lg:hidden"
            onClick={onClose}
          />
          <motion.aside
            initial={{ x: "-100%" }}
            animate={{ x: 0 }}
            exit={{ x: "-100%" }}
            transition={{ duration: 0.28, ease: [0.16, 1, 0.3, 1] }}
            className="fixed inset-y-0 left-0 z-50 flex w-72 flex-col bg-white shadow-[var(--shadow-float)] lg:hidden"
          >
            <div className="flex h-16 items-center justify-between border-b border-charcoal-200 px-5">
              <div className="flex items-center gap-2.5">
                <LogoMark />
                <Wordmark className="text-base" />
              </div>
              <button onClick={onClose} className="flex size-8 items-center justify-center rounded-full hover:bg-charcoal-100" aria-label="Close menu">
                <X className="size-4" />
              </button>
            </div>
            <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-5">
              {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
                <NavLink
                  key={to}
                  to={to}
                  onClick={onClose}
                  className={({ isActive }) =>
                    cn(
                      "flex items-center gap-3 rounded-lg px-3 py-2.5 text-[13px] font-medium transition-colors",
                      isActive ? "bg-nile-900 text-white" : "text-charcoal-600 hover:bg-charcoal-100"
                    )
                  }
                >
                  <Icon className="size-4" />
                  {label}
                </NavLink>
              ))}
            </nav>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  );
}
