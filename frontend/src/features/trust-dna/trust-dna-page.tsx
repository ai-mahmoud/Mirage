import { useQuery } from "@tanstack/react-query";
import { TrustDNACard } from "@/components/dashboard/trust-dna-card";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { NoActiveSession } from "@/components/shared/no-active-session";
import { TRUST_DNA_LABELS } from "@/data/demo-data";
import { getTrustStatus } from "@/lib/api-client";
import { mapTrustDna } from "@/lib/session-mappers";
import { useCurrentSession } from "@/contexts/session-context";
import type { TrustDNA } from "@/types/domain";

export function TrustDnaPage() {
  const { currentSessionId } = useCurrentSession();
  const { data } = useQuery({
    queryKey: ["session-trust", currentSessionId],
    queryFn: () => getTrustStatus(currentSessionId as string),
    enabled: !!currentSessionId,
    refetchInterval: 1000,
  });

  if (!currentSessionId) return <NoActiveSession />;
  if (!data) return <p className="text-sm text-charcoal-500">Loading Trust DNA…</p>;

  const trustDNA = mapTrustDna(data.trustDna);
  const entries = Object.entries(trustDNA) as [keyof TrustDNA, number][];

  return (
    <div className="grid gap-6 xl:grid-cols-3">
      <div className="xl:col-span-1">
        <TrustDNACard trustDNA={trustDNA} />
      </div>

      <div className="space-y-6 xl:col-span-2">
        <Card>
          <CardHeader>
            <div>
              <CardTitle>Dimension Definitions</CardTitle>
              <CardDescription>
                The Trust DNA replaces a single trust score with six independently-evolving dimensions —
                inspired by the Weighing of the Heart: no single measure decides the outcome.
              </CardDescription>
            </div>
          </CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-2">
            {entries.map(([key, value]) => (
              <div key={key} className="rounded-lg border border-charcoal-100 p-4">
                <div className="flex items-baseline justify-between">
                  <h4 className="text-sm font-semibold text-charcoal-800">{TRUST_DNA_LABELS[key].label}</h4>
                  <span className="tabular text-sm font-semibold text-nile-800">{Math.round(value)}</span>
                </div>
                <p className="mt-1.5 text-xs leading-relaxed text-charcoal-500">{TRUST_DNA_LABELS[key].description}</p>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Weighting Model</CardTitle>
            <CardDescription>Initial MVP heuristic — configurable, not a fixed constant.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 text-sm">
              {[
                ["Behavioral Consistency", "25%"],
                ["Interaction Naturalness", "20%"],
                ["Attention Stability", "20%"],
                ["Context Integrity", "15%"],
                ["Adaptive Responsiveness", "10%"],
                ["Session Authenticity Synthesis", "10%"],
              ].map(([label, weight]) => (
                <div key={label} className="flex items-center justify-between border-b border-charcoal-100 py-2 last:border-0">
                  <span className="text-charcoal-600">{label}</span>
                  <span className="tabular font-medium text-charcoal-800">{weight}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
