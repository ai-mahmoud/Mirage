import { motion } from "framer-motion";
import type { TrustDNA } from "@/types/domain";
import { TRUST_DNA_LABELS } from "@/data/demo-data";
import { ProgressBar, RadialGauge } from "@/components/ui/progress";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";

const DIMENSION_TONE: Record<keyof TrustDNA, "nile" | "gold" | "turquoise" | "emerald" | "amber" | "crimson"> = {
  behavioralConsistency: "nile",
  attentionStability: "turquoise",
  interactionNaturalness: "gold",
  contextIntegrity: "emerald",
  adaptiveResponsiveness: "amber",
  sessionAuthenticity: "nile",
};

export function TrustDNACard({ trustDNA, compact }: { trustDNA: TrustDNA; compact?: boolean }) {
  const dimensions = Object.entries(trustDNA) as [keyof TrustDNA, number][];
  const synthesis = trustDNA.sessionAuthenticity;

  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle>Trust DNA</CardTitle>
          <CardDescription>Six independent behavioral dimensions — evaluated together, never in isolation.</CardDescription>
        </div>
        {!compact && <RadialGauge value={synthesis} tone="nile" label="Synthesis" />}
      </CardHeader>
      <CardContent className="space-y-4">
        {dimensions
          .filter(([key]) => key !== "sessionAuthenticity")
          .map(([key, value], i) => (
            <motion.div
              key={key}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
            >
              <div className="mb-1.5 flex items-baseline justify-between">
                <span className="text-[13px] font-medium text-charcoal-700">{TRUST_DNA_LABELS[key].label}</span>
                <span className="tabular text-[13px] font-semibold text-charcoal-800">{value}</span>
              </div>
              <ProgressBar value={value} tone={DIMENSION_TONE[key]} />
            </motion.div>
          ))}
      </CardContent>
    </Card>
  );
}
