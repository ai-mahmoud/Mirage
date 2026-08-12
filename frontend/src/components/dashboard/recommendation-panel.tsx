import { motion } from "framer-motion";
import { Scale, ShieldCheck, Eye } from "lucide-react";
import type { Recommendation } from "@/types/domain";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { RadialGauge } from "@/components/ui/progress";
import { RECOMMENDATION_META, bandFromScore, BAND_META } from "@/lib/confidence";

export function DecisionConfidenceCard({ confidence }: { confidence: number }) {
  const band = bandFromScore(confidence);
  const meta = BAND_META[band];
  return (
    <Card interactive>
      <CardHeader>
        <div>
          <CardTitle>Decision Confidence</CardTitle>
          <CardDescription>How strongly evidence supports the current recommendation.</CardDescription>
        </div>
        <Badge tone={meta.tone}>{meta.label}</Badge>
      </CardHeader>
      <CardContent className="flex items-center gap-6">
        <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}>
          <RadialGauge value={confidence} size={112} strokeWidth={10} tone={meta.color as never} label="Confidence" />
        </motion.div>
        <div className="space-y-1.5 text-xs leading-relaxed text-charcoal-500">
          <p>Evidence Confidence and Recommendation Confidence are calculated independently to avoid overclaiming certainty.</p>
        </div>
      </CardContent>
    </Card>
  );
}

export function RecommendationPanel({
  recommendation,
  onContinue,
  onGenerateReport,
}: {
  recommendation: Recommendation;
  onContinue?: () => void;
  onGenerateReport?: () => void;
}) {
  const meta = RECOMMENDATION_META[recommendation.action];
  return (
    <Card className="overflow-hidden border-nile-100">
      <div className="h-1 w-full bg-gradient-to-r from-nile-900 via-turquoise-500 to-gold-500" />
      <CardHeader>
        <div className="flex items-center gap-2">
          <span className="flex size-8 items-center justify-center rounded-full bg-nile-50 text-nile-800">
            <Scale className="size-4" />
          </span>
          <CardTitle>Recommendation</CardTitle>
        </div>
        <Badge tone={meta.tone}>{meta.label}</Badge>
      </CardHeader>
      <CardContent>
        <p className="text-lg font-semibold tracking-tight text-charcoal-900">{recommendation.label}</p>
        <ul className="mt-3.5 space-y-2">
          {recommendation.reasons.map((r, i) => (
            <motion.li
              key={r}
              initial={{ opacity: 0, x: -6 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.08 }}
              className="flex items-start gap-2.5 text-sm text-charcoal-600"
            >
              <span className="mt-1.5 size-1 shrink-0 rounded-full bg-nile-700" />
              {r}
            </motion.li>
          ))}
        </ul>
        <div className="mt-4 flex items-center gap-2.5 rounded-lg bg-nile-50 px-3.5 py-2.5 text-xs leading-relaxed text-nile-900">
          <ShieldCheck className="size-4 shrink-0" />
          Human decision support — not an automated decision. Final authority remains with the reviewer.
        </div>
        <div className="mt-5 flex gap-3">
          <Button variant="secondary" size="sm" onClick={onContinue} className="gap-1.5">
            <Eye className="size-3.5" /> Continue Monitoring
          </Button>
          <Button variant="primary" size="sm" onClick={onGenerateReport}>
            Generate Report
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
