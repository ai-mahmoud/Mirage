import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

export function ProgressBar({
  value,
  className,
  tone = "nile",
  height = 8,
}: {
  value: number;
  className?: string;
  tone?: "nile" | "gold" | "turquoise" | "emerald" | "amber" | "crimson";
  height?: number;
}) {
  const toneMap: Record<string, string> = {
    nile: "bg-nile-700",
    gold: "bg-gold-500",
    turquoise: "bg-turquoise-500",
    emerald: "bg-emerald-500",
    amber: "bg-amber-500",
    crimson: "bg-crimson-500",
  };
  return (
    <div
      className={cn("w-full overflow-hidden rounded-full bg-charcoal-100", className)}
      style={{ height }}
      role="progressbar"
      aria-valuenow={value}
      aria-valuemin={0}
      aria-valuemax={100}
    >
      <motion.div
        className={cn("h-full rounded-full", toneMap[tone])}
        initial={{ width: 0 }}
        animate={{ width: `${Math.min(100, Math.max(0, value))}%` }}
        transition={{ duration: 0.6, ease: "easeOut" }}
      />
    </div>
  );
}

export function RadialGauge({
  value,
  size = 88,
  strokeWidth = 8,
  tone = "nile",
  label,
}: {
  value: number;
  size?: number;
  strokeWidth?: number;
  tone?: "nile" | "gold" | "turquoise" | "emerald" | "amber" | "crimson";
  label?: string;
}) {
  const toneMap: Record<string, string> = {
    nile: "stroke-nile-700",
    gold: "stroke-gold-500",
    turquoise: "stroke-turquoise-500",
    emerald: "stroke-emerald-500",
    amber: "stroke-amber-500",
    crimson: "stroke-crimson-500",
  };
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (Math.min(100, Math.max(0, value)) / 100) * circumference;

  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={radius} strokeWidth={strokeWidth} className="stroke-charcoal-100" fill="none" />
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          strokeWidth={strokeWidth}
          fill="none"
          strokeLinecap="round"
          className={toneMap[tone]}
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 0.9, ease: "easeOut" }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="tabular text-lg font-semibold text-charcoal-800">{Math.round(value)}</span>
        {label && <span className="text-[10px] text-charcoal-500">{label}</span>}
      </div>
    </div>
  );
}
