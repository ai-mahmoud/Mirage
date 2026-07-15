import * as React from "react";
import { AnimatePresence } from "framer-motion";
import { CheckCircle2, Loader2 } from "lucide-react";
import { RadialGauge } from "@/components/ui/progress";

const STAGES = [
  "Initializing Tracking",
  "Loading AI Models",
  "Creating Behavioral Context",
  "Starting Secure Session",
  "Behavior Engine Ready",
];

export function SessionInitializing({ onComplete }: { onComplete: () => void }) {
  const [stage, setStage] = React.useState(0);

  React.useEffect(() => {
    if (stage >= STAGES.length) {
      const t = setTimeout(onComplete, 400);
      return () => clearTimeout(t);
    }
    const t = setTimeout(() => setStage((s) => s + 1), 620);
    return () => clearTimeout(t);
  }, [stage, onComplete]);

  const progress = Math.min(100, (stage / STAGES.length) * 100);

  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center">
      <RadialGauge value={progress} size={120} strokeWidth={8} tone="turquoise" label="Ready" />
      <div className="mt-8 w-full max-w-xs space-y-3">
        {STAGES.map((label, i) => (
          <div key={label} className="flex items-center gap-3 text-sm">
            {i < stage ? (
              <CheckCircle2 className="size-4 text-emerald-600" />
            ) : i === stage ? (
              <Loader2 className="size-4 animate-spin text-nile-700" />
            ) : (
              <span className="size-4 rounded-full border border-charcoal-200" />
            )}
            <span className={i <= stage ? "text-charcoal-800" : "text-charcoal-400"}>{label}</span>
          </div>
        ))}
      </div>
      <AnimatePresence />
    </div>
  );
}
