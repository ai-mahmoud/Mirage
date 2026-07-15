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
    <Card>
      <CardHeader>
        <div>
          <CardTitle>Decision Confidence</CardTitle>
          <CardDescription>How strongly evidence supports the current recommendation.</CardDescription>
        </div>
        <Badge tone={meta.tone}>{meta.label}</Badge>
      </CardHeader>
      <CardContent className="flex items-center gap-6">
        <RadialGauge value={confidence} size={104} strokeWidth={10} tone={meta.color as never} label="Confidence" />
        <div className="space-y-1.5 text-xs text-charcoal-500">
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
    <Card className="border-nile-100">
      <CardHeader>
        <div className="flex items-center gap-2">
          <Scale className="size-4 text-nile-800" />
          <CardTitle>Recommendation</CardTitle>
        </div>
        <Badge tone={meta.tone}>{meta.label}</Badge>
      </CardHeader>
      <CardContent>
        <p className="text-base font-semibold text-charcoal-800">{recommendation.label}</p>
        <ul className="mt-3 space-y-1.5">
          {recommendation.reasons.map((r) => (
            <li key={r} className="flex items-start gap-2 text-sm text-charcoal-600">
              <span className="mt-1.5 size-1 shrink-0 rounded-full bg-nile-700" />
              {r}
            </li>
          ))}
        </ul>
        <div className="mt-4 flex items-center gap-2 rounded-lg bg-nile-50 px-3 py-2 text-xs text-nile-900">
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
