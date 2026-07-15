import type { ConfidenceBand, RecommendationAction, SeverityLevel } from "@/types/domain";

export function bandFromScore(score: number): ConfidenceBand {
  if (score >= 90) return "very-high";
  if (score >= 78) return "high";
  if (score >= 60) return "moderate";
  if (score >= 40) return "low";
  return "very-low";
}

export const BAND_META: Record<ConfidenceBand, { label: string; tone: "success" | "turquoise" | "warning" | "danger"; color: string }> = {
  "very-high": { label: "Very High", tone: "success", color: "emerald" },
  high: { label: "High", tone: "success", color: "emerald" },
  moderate: { label: "Moderate", tone: "warning", color: "amber" },
  low: { label: "Low", tone: "danger", color: "crimson" },
  "very-low": { label: "Very Low", tone: "danger", color: "crimson" },
};

export const SEVERITY_META: Record<SeverityLevel, { label: string; tone: "neutral" | "warning" | "danger" }> = {
  low: { label: "Low", tone: "neutral" },
  medium: { label: "Medium", tone: "warning" },
  high: { label: "High", tone: "danger" },
};

export const RECOMMENDATION_META: Record<RecommendationAction, { label: string; tone: "success" | "turquoise" | "warning" | "danger" }> = {
  "proceed-normally": { label: "Proceed Normally", tone: "success" },
  "continue-monitoring": { label: "Continue Monitoring", tone: "turquoise" },
  "additional-evidence": { label: "Additional Evidence Recommended", tone: "warning" },
  "manual-review": { label: "Manual Review Recommended", tone: "warning" },
  "high-risk-investigation": { label: "High-Risk Investigation", tone: "danger" },
};
