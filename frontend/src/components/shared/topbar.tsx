import { Bell, ChevronDown, Menu } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { useAuth } from "@/contexts/auth-context";

export function Topbar({ title, subtitle, onMenuClick }: { title: string; subtitle?: string; onMenuClick?: () => void }) {
  const { user } = useAuth();
  return (
    <header className="sticky top-0 z-10 flex h-16 items-center justify-between border-b border-charcoal-200 bg-white/90 px-4 backdrop-blur sm:px-6">
      <div className="flex items-center gap-3">
        <button
          onClick={onMenuClick}
          className="flex size-9 items-center justify-center rounded-full text-charcoal-600 hover:bg-charcoal-100 lg:hidden"
          aria-label="Open menu"
        >
          <Menu className="size-5" />
        </button>
        <div>
          <h1 className="text-[15px] font-semibold text-charcoal-900">{title}</h1>
          {subtitle && <p className="hidden text-xs text-charcoal-500 sm:block">{subtitle}</p>}
        </div>
      </div>

      <div className="flex items-center gap-2.5 sm:gap-4">
        <Badge tone="success" dot className="hidden sm:inline-flex">
          System Operational
        </Badge>
        <button
          className="relative flex size-9 items-center justify-center rounded-full text-charcoal-500 transition-colors hover:bg-charcoal-100"
          aria-label="Notifications"
        >
          <Bell className="size-4.5" />
          <span className="absolute right-2 top-2 size-1.5 rounded-full bg-crimson-500" />
        </button>
        <button className="flex items-center gap-2 rounded-full py-1 pl-1 pr-2 transition-colors hover:bg-charcoal-100">
          <span className="flex size-8 items-center justify-center rounded-full bg-nile-900 text-xs font-semibold text-white">
            {user?.initials ?? "DU"}
          </span>
          <span className="hidden text-[13px] font-medium text-charcoal-700 sm:inline">{user?.name ?? "Demo User"}</span>
          <ChevronDown className="hidden size-3.5 text-charcoal-400 sm:inline" />
        </button>
      </div>
    </header>
  );
}
