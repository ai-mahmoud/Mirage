import { motion, AnimatePresence } from "framer-motion";
import { Feather } from "lucide-react";
import type { EvidenceItem } from "@/types/domain";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SEVERITY_META } from "@/lib/confidence";

function timeAgo(iso: string) {
  const diff = Math.max(0, Date.now() - new Date(iso).getTime());
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins === 1) return "1 min ago";
  return `${mins} min ago`;
}

export function EvidenceCard({ evidence, index }: { evidence: EvidenceItem; index: number }) {
  const sev = SEVERITY_META[evidence.severity];
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.06, duration: 0.35 }}
      className="rounded-[var(--radius-card)] border border-charcoal-200 bg-white p-4"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <div className="mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-full bg-gold-100 text-gold-700">
            <Feather className="size-4" />
          </div>
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-charcoal-500">
              Evidence #{evidence.index} · {evidence.category}
            </p>
            <h4 className="mt-0.5 text-sm font-semibold text-charcoal-800">{evidence.title}</h4>
          </div>
        </div>
        <Badge tone={sev.tone === "neutral" ? "neutral" : sev.tone}>{sev.label}</Badge>
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
    </motion.div>
  );
}

export function EvidenceFeed({ items, title = "Evidence Feed", description = "Evidence appears before any recommendation." }: { items: EvidenceItem[]; title?: string; description?: string }) {
  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle>{title}</CardTitle>
          <CardDescription>{description}</CardDescription>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <AnimatePresence initial={false}>
          {items.map((item, i) => (
            <EvidenceCard evidence={item} index={i} key={item.id} />
          ))}
        </AnimatePresence>
      </CardContent>
    </Card>
  );
}
