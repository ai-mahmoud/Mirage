import { motion } from "framer-motion";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { ProgressBar } from "@/components/ui/progress";
import { NoActiveSession } from "@/components/shared/no-active-session";
import { TRUST_DNA_LABELS } from "@/data/demo-data";
import type { TrustDNA } from "@/types/domain";
import { TrustDnaHero } from "@/features/trust-dna/trust-dna-hero";
import { getTrustStatus } from "@/lib/api-client";
import { mapTrustDna } from "@/lib/session-mappers";
import { useCurrentSession } from "@/contexts/session-context";

const DIMENSION_TONE: Record<keyof TrustDNA, "nile" | "gold" | "turquoise" | "emerald" | "amber" | "crimson"> = {
  behavioralConsistency: "nile",
  attentionStability: "turquoise",
  interactionNaturalness: "gold",
  contextIntegrity: "emerald",
  adaptiveResponsiveness: "amber",
  sessionAuthenticity: "nile",
};

const WEIGHTS: [string, string][] = [
  ["Behavioral Consistency", "25%"],
  ["Interaction Naturalness", "20%"],
  ["Attention Stability", "20%"],
  ["Context Integrity", "15%"],
  ["Adaptive Responsiveness", "10%"],
  ["Session Authenticity Synthesis", "10%"],
];

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
  const entries = (Object.entries(trustDNA) as [keyof TrustDNA, number][]).filter(
    ([key]) => key !== "sessionAuthenticity"
  );

  return (
    <div className="space-y-6">
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
        <TrustDnaHero trustDNA={trustDNA} />
      </motion.div>

      <div className="grid gap-6 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader>
            <div>
              <CardTitle>Dimension Detail</CardTitle>
              <CardDescription>
                No single measure decides the outcome — each dimension evolves independently across the session.
              </CardDescription>
            </div>
          </CardHeader>
          <CardContent className="grid gap-5 sm:grid-cols-2">
            {entries.map(([key, value], i) => (
              <motion.div
                key={key}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 + i * 0.06 }}
                className="card-hover rounded-xl border border-charcoal-100 p-4"
              >
                <div className="flex items-baseline justify-between">
                  <h4 className="text-sm font-semibold text-charcoal-800">{TRUST_DNA_LABELS[key].label}</h4>
                  <span className="tabular text-sm font-semibold text-nile-800">{Math.round(value)}</span>
                </div>
                <p className="mt-1.5 text-xs leading-relaxed text-charcoal-500">{TRUST_DNA_LABELS[key].description}</p>
                <div className="mt-3">
                  <ProgressBar value={value} tone={DIMENSION_TONE[key]} height={6} />
                </div>
              </motion.div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Weighting Model</CardTitle>
            <CardDescription>Initial MVP heuristic — configurable, not a fixed constant.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-1">
            {WEIGHTS.map(([label, weight], i) => (
              <motion.div
                key={label}
                initial={{ opacity: 0, x: -6 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.15 + i * 0.05 }}
                className="flex items-center justify-between border-b border-charcoal-100 py-2.5 text-sm last:border-0"
              >
                <span className="text-charcoal-600">{label}</span>
                <span className="tabular font-medium text-charcoal-800">{weight}</span>
              </motion.div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
