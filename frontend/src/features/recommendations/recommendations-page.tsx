import { useQuery } from "@tanstack/react-query";
import { DecisionConfidenceCard, RecommendationPanel } from "@/components/dashboard/recommendation-panel";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { NoActiveSession } from "@/components/shared/no-active-session";
import { getTrustStatus } from "@/lib/api-client";
import { mapRecommendation } from "@/lib/session-mappers";
import { useCurrentSession } from "@/contexts/session-context";
import { RECOMMENDATION_META } from "@/lib/confidence";
import type { RecommendationAction } from "@/types/domain";

const DECISION_MAP: { confidence: string; action: RecommendationAction }[] = [
  { confidence: "Very High", action: "proceed-normally" },
  { confidence: "High", action: "continue-monitoring" },
  { confidence: "Moderate", action: "additional-evidence" },
  { confidence: "Low", action: "manual-review" },
  { confidence: "Very Low", action: "high-risk-investigation" },
];

export function RecommendationsPage() {
  const { currentSessionId } = useCurrentSession();
  const { data } = useQuery({
    queryKey: ["session-trust", currentSessionId],
    queryFn: () => getTrustStatus(currentSessionId as string),
    enabled: !!currentSessionId,
    refetchInterval: 1000,
  });

  if (!currentSessionId) return <NoActiveSession />;
  if (!data) return <p className="text-sm text-charcoal-500">Loading recommendation…</p>;

  const recommendation = mapRecommendation(data.recommendation, data.recommendationConfidence);

  return (
    <div className="grid gap-6 xl:grid-cols-3">
      <div className="space-y-6 xl:col-span-2">
        <RecommendationPanel recommendation={recommendation} />
        <Card>
          <CardHeader>
            <div>
              <CardTitle>Decision Mapping</CardTitle>
              <CardDescription>The framework recommends actions — it never issues definitive judgments.</CardDescription>
            </div>
          </CardHeader>
          <CardContent className="space-y-2">
            {DECISION_MAP.map(({ confidence, action }) => {
              const meta = RECOMMENDATION_META[action];
              return (
                <div key={confidence} className="flex items-center justify-between border-b border-charcoal-100 py-2.5 last:border-0">
                  <span className="text-sm text-charcoal-600">{confidence} Decision Confidence</span>
                  <Badge tone={meta.tone}>{meta.label}</Badge>
                </div>
              );
            })}
          </CardContent>
        </Card>
      </div>
      <div>
        <DecisionConfidenceCard confidence={recommendation.confidence} />
      </div>
    </div>
  );
}
