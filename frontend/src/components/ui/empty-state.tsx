import type { LucideIcon } from "lucide-react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  className,
}: {
  icon: LucideIcon;
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      className={cn("flex flex-col items-center justify-center rounded-[var(--radius-card)] border border-dashed border-charcoal-200 bg-charcoal-50/40 px-6 py-14 text-center", className)}
    >
      <div className="flex size-12 items-center justify-center rounded-full bg-nile-50 text-nile-700">
        <Icon className="size-5" />
      </div>
      <h3 className="mt-4 text-sm font-semibold text-charcoal-800">{title}</h3>
      {description && <p className="mt-1.5 max-w-xs text-xs leading-relaxed text-charcoal-500">{description}</p>}
      {action && <div className="mt-5">{action}</div>}
    </motion.div>
  );
}
