import { motion } from "framer-motion";
import * as React from "react";
import type { TrustDNA } from "@/types/domain";
import { TRUST_DNA_LABELS } from "@/data/demo-data";
import { RadialGauge } from "@/components/ui/progress";
import { cn } from "@/lib/utils";

const DIMENSION_TONE: Record<keyof TrustDNA, { ring: string; text: string; dot: string }> = {
  behavioralConsistency: { ring: "nile", text: "text-nile-800", dot: "bg-nile-700" },
  attentionStability: { ring: "turquoise", text: "text-turquoise-700", dot: "bg-turquoise-500" },
  interactionNaturalness: { ring: "gold", text: "text-gold-700", dot: "bg-gold-500" },
  contextIntegrity: { ring: "emerald", text: "text-emerald-700", dot: "bg-emerald-500" },
  adaptiveResponsiveness: { ring: "amber", text: "text-amber-700", dot: "bg-amber-500" },
  sessionAuthenticity: { ring: "nile", text: "text-nile-800", dot: "bg-nile-700" },
} as const;

export function TrustDnaHero({ trustDNA }: { trustDNA: TrustDNA }) {
  const [active, setActive] = React.useState<keyof TrustDNA | null>(null);
  const dimensions = (Object.entries(trustDNA) as [keyof TrustDNA, number][]).filter(
    ([key]) => key !== "sessionAuthenticity"
  );

  return (
    <div className="relative overflow-hidden rounded-[24px] border border-charcoal-200 bg-gradient-to-b from-white to-nile-50/40 px-6 py-12 sm:px-12">
      <div className="bg-grid-faint absolute inset-0 opacity-[0.25] [mask-image:radial-gradient(ellipse_55%_55%_at_50%_40%,black,transparent)]" />

      <div className="relative flex flex-col items-center">
        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-gold-600">Weighing of the Heart</p>
        <h2 className="mt-2 text-2xl font-semibold tracking-tight text-charcoal-900">Trust DNA</h2>
        <p className="mt-1.5 max-w-md text-center text-sm text-charcoal-500">
          Six independent dimensions, evaluated together. Hover a node to inspect it.
        </p>

        {/* Radial cluster */}
        <div className="relative mt-10 flex h-[340px] w-full max-w-[420px] items-center justify-center sm:h-[380px]">
          {/* Center synthesis gauge */}
          <motion.div
            initial={{ scale: 0.85, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
            className="z-10 flex flex-col items-center justify-center rounded-full bg-white p-2 shadow-[var(--shadow-float)]"
          >
            <RadialGauge value={trustDNA.sessionAuthenticity} size={148} strokeWidth={11} tone="nile" label="Synthesis" />
          </motion.div>

          {/* Orbiting dimension nodes */}
          {dimensions.map(([key, value], i) => {
            const angle = (i / dimensions.length) * 2 * Math.PI - Math.PI / 2;
            const radius = 168;
            const x = Math.cos(angle) * radius;
            const y = Math.sin(angle) * radius;
            const tone = DIMENSION_TONE[key];
            const isActive = active === key;

            return (
              <motion.button
                key={key}
                type="button"
                onMouseEnter={() => setActive(key)}
                onMouseLeave={() => setActive(null)}
                onFocus={() => setActive(key)}
                onBlur={() => setActive(null)}
                initial={{ opacity: 0, scale: 0.6 }}
                animate={{
                  opacity: 1,
                  scale: isActive ? 1.12 : 1,
                  x,
                  y,
                }}
                transition={{ duration: 0.5, delay: 0.15 + i * 0.08, ease: [0.16, 1, 0.3, 1] }}
                className="absolute flex flex-col items-center"
                style={{ left: "50%", top: "50%", marginLeft: -40, marginTop: -40 }}
              >
                <span
                  className={cn(
                    "flex size-20 items-center justify-center rounded-full border-2 bg-white text-center shadow-md transition-shadow",
                    isActive ? "border-current shadow-lg" : "border-charcoal-100",
                    tone.text
                  )}
                >
                  <span className="flex flex-col items-center">
                    <span className="tabular text-lg font-semibold text-charcoal-800">{value}</span>
                    <span className={cn("mt-0.5 size-1.5 rounded-full", tone.dot)} />
                  </span>
                </span>
                <span
                  className={cn(
                    "mt-2 max-w-[92px] text-center text-[10.5px] font-medium leading-tight transition-colors",
                    isActive ? "text-charcoal-800" : "text-charcoal-400"
                  )}
                >
                  {TRUST_DNA_LABELS[key].label}
                </span>
              </motion.button>
            );
          })}
        </div>

        {/* Active detail panel */}
        <div className="mt-8 flex h-14 max-w-md items-center justify-center text-center">
          {active ? (
            <motion.p
              key={active}
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-sm text-charcoal-600"
            >
              <span className="font-semibold text-charcoal-800">{TRUST_DNA_LABELS[active].label}:</span>{" "}
              {TRUST_DNA_LABELS[active].description}
            </motion.p>
          ) : (
            <p className="text-sm text-charcoal-400">Hover any dimension to read its definition.</p>
          )}
        </div>
      </div>
    </div>
  );
}
