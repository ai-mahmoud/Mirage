import { Bell, ChevronDown } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { useAuth } from "@/contexts/auth-context";

export function Topbar({ title, subtitle }: { title: string; subtitle?: string }) {
  const { user } = useAuth();
  return (
    <header className="sticky top-0 z-10 flex h-16 items-center justify-between border-b border-charcoal-200 bg-white/90 px-6 backdrop-blur">
      <div>
        <h1 className="text-[15px] font-semibold text-charcoal-900">{title}</h1>
        {subtitle && <p className="text-xs text-charcoal-500">{subtitle}</p>}
      </div>

      <div className="flex items-center gap-4">
        <Badge tone="success" dot>
          System Operational
        </Badge>
        <button
          className="relative flex size-9 items-center justify-center rounded-full text-charcoal-500 hover:bg-charcoal-100"
          aria-label="Notifications"
        >
          <Bell className="size-4.5" />
        </button>
        <button className="flex items-center gap-2 rounded-full py-1 pl-1 pr-2 hover:bg-charcoal-100">
          <span className="flex size-8 items-center justify-center rounded-full bg-nile-900 text-xs font-semibold text-white">
            {user?.initials ?? "DU"}
          </span>
          <span className="hidden text-[13px] font-medium text-charcoal-700 sm:inline">{user?.name ?? "Demo User"}</span>
          <ChevronDown className="size-3.5 text-charcoal-400" />
        </button>
      </div>
    </header>
  );
}
