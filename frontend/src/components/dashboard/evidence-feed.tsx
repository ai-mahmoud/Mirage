import { motion, AnimatePresence } from "framer-motion";
import { Feather } from "lucide-react";
import type { EvidenceItem } from "@/types/domain";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SEVERITY_META } from "@/lib/confidence";
import { EmptyState } from "@/components/ui/empty-state";
import { cn } from "@/lib/utils";

function timeAgo(iso: string) {
  const diff = Math.max(0, Date.now() - new Date(iso).getTime());
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins === 1) return "1 min ago";
  return `${mins} min ago`;
}

const SEVERITY_DOT: Record<string, string> = {
  low: "bg-turquoise-500",
  medium: "bg-amber-500",
  high: "bg-crimson-500",
};

export function EvidenceCard({ evidence, index, isLast }: { evidence: EvidenceItem; index: number; isLast?: boolean }) {
  const sev = SEVERITY_META[evidence.severity];
  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.06, duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
      className="relative flex gap-4"
    >
      {/* Timeline rail */}
      <div className="flex flex-col items-center">
        <span className="flex size-9 shrink-0 items-center justify-center rounded-full bg-gold-100 text-gold-700 ring-4 ring-white">
          <Feather className="size-4" />
        </span>
        {!isLast && <span className="mt-1 w-px flex-1 bg-charcoal-200" />}
      </div>

      <div className={cn("card-hover mb-5 flex-1 rounded-[var(--radius-card)] border border-charcoal-200 bg-white p-4")}>
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-[11px] font-medium uppercase tracking-wide text-charcoal-500">
              Evidence #{evidence.index} · {evidence.category}
            </p>
            <h4 className="mt-0.5 text-sm font-semibold text-charcoal-800">{evidence.title}</h4>
          </div>
          <Badge tone={sev.tone === "neutral" ? "neutral" : sev.tone} className="shrink-0">
            <span className={cn("size-1.5 rounded-full", SEVERITY_DOT[evidence.severity])} />
            {sev.label}
          </Badge>
        </div>

        <p className="mt-3 text-sm leading-relaxed text-charcoal-600">{evidence.observation}</p>

        <ul className="mt-3 space-y-1">
          {evidence.supportingSignals.map((s) => (
            <li key={s} className="flex items-start gap-2 text-xs text-charcoal-500">
              <span className="mt-1.5 size-1 shrink-0 rounded-full bg-charcoal-300" />
              {s}
            </li>
          ))}
        </ul>

        <div className="mt-4 flex items-center justify-between border-t border-charcoal-100 pt-3">
          <span className="text-xs text-charcoal-500">{timeAgo(evidence.timestamp)}</span>
          <span className="tabular text-xs font-semibold text-nile-800">Confidence {evidence.confidence}%</span>
        </div>
      </div>
    </motion.div>
  );
}

export function EvidenceFeed({
  items,
  title = "Evidence Feed",
  description = "Evidence appears before any recommendation.",
}: {
  items: EvidenceItem[];
  title?: string;
  description?: string;
}) {
  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle>{title}</CardTitle>
          <CardDescription>{description}</CardDescription>
        </div>
      </CardHeader>
      <CardContent>
        {items.length === 0 ? (
          <EmptyState icon={Feather} title="No evidence yet" description="Evidence appears here as the session generates supporting observations." />
        ) : (
          <AnimatePresence initial={false}>
            {items.map((item, i) => (
              <EvidenceCard evidence={item} index={i} isLast={i === items.length - 1} key={item.id} />
            ))}
          </AnimatePresence>
        )}
      </CardContent>
    </Card>
  );
}
