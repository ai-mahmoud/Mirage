import { NavLink } from "react-router-dom";
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
];

export function Sidebar() {
  return (
    <aside className="hidden w-64 shrink-0 flex-col border-r border-charcoal-200 bg-white lg:flex">
      <div className="flex h-16 items-center gap-2.5 border-b border-charcoal-200 px-6">
        <LogoMark />
        <Wordmark className="text-base" />
      </div>

      <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-5">
        {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-[13px] font-medium transition-colors",
                isActive
                  ? "bg-nile-900 text-white shadow-sm"
                  : "text-charcoal-600 hover:bg-charcoal-100 hover:text-charcoal-900"
              )
            }
          >
            <Icon className="size-4" />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="border-t border-charcoal-200 p-3">
        <NavLink
          to="/settings"
          className={({ isActive }) =>
            cn(
              "flex items-center gap-3 rounded-lg px-3 py-2.5 text-[13px] font-medium transition-colors",
              isActive ? "bg-nile-900 text-white" : "text-charcoal-600 hover:bg-charcoal-100"
            )
          }
        >
          <Settings className="size-4" />
          Settings
        </NavLink>
      </div>
    </aside>
  );
}
