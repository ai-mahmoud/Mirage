import { useQuery } from "@tanstack/react-query";
import { BehaviorTimeline } from "@/components/dashboard/behavior-timeline";
import { NoActiveSession } from "@/components/shared/no-active-session";
import { getTrustStatus } from "@/lib/api-client";
import { deriveTimelineFromEvidence, mapEvidenceList } from "@/lib/session-mappers";
import { useCurrentSession } from "@/contexts/session-context";

export function TimelinePage() {
  const { currentSessionId } = useCurrentSession();
  const { data } = useQuery({
    queryKey: ["session-trust", currentSessionId],
    queryFn: () => getTrustStatus(currentSessionId as string),
    enabled: !!currentSessionId,
    refetchInterval: 1000,
  });

  if (!currentSessionId) return <NoActiveSession />;
  if (!data) return <p className="text-sm text-charcoal-500">Loading timeline…</p>;

  const timeline = deriveTimelineFromEvidence(mapEvidenceList(data.evidence));

  return (
    <div className="mx-auto max-w-2xl">
      <BehaviorTimeline events={timeline} />
    </div>
  );
}
