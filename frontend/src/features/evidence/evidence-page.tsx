import { useQuery } from "@tanstack/react-query";
import { EvidenceFeed } from "@/components/dashboard/evidence-feed";
import { Card, CardContent } from "@/components/ui/card";
import { NoActiveSession } from "@/components/shared/no-active-session";
import { getTrustStatus } from "@/lib/api-client";
import { mapEvidenceList } from "@/lib/session-mappers";
import { useCurrentSession } from "@/contexts/session-context";

export function EvidencePage() {
  const { currentSessionId } = useCurrentSession();
  const { data } = useQuery({
    queryKey: ["session-trust", currentSessionId],
    queryFn: () => getTrustStatus(currentSessionId as string),
    enabled: !!currentSessionId,
    refetchInterval: 1000,
  });

  if (!currentSessionId) return <NoActiveSession />;
  if (!data) return <p className="text-sm text-charcoal-500">Loading evidence…</p>;

  const evidence = mapEvidenceList(data.evidence);
  const avgConfidence = evidence.length
    ? Math.round(evidence.reduce((a, e) => a + e.confidence, 0) / evidence.length)
    : 0;

  return (
    <div className="grid gap-6 xl:grid-cols-3">
      <div className="space-y-6 xl:col-span-2">
        <EvidenceFeed items={evidence} />
      </div>
      <div className="space-y-6">
        <Card>
          <CardContent className="p-5">
            <p className="text-xs font-medium text-charcoal-500">Evidence Items</p>
            <p className="tabular mt-2 text-3xl font-semibold text-charcoal-900">{evidence.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-5">
            <p className="text-xs font-medium text-charcoal-500">Average Evidence Confidence</p>
            <p className="tabular mt-2 text-3xl font-semibold text-nile-800">{evidence.length ? `${avgConfidence}%` : "—"}</p>
          </CardContent>
        </Card>
        <Card className="bg-nile-50 border-nile-100">
          <CardContent className="p-5 text-xs leading-relaxed text-nile-900">
            Evidence always appears before any recommendation. The platform never states a conclusion without
            the supporting observations attached to it.
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
