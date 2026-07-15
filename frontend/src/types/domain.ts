// Core domain model — mirrors the Unified Behavioral Data Model (UBDM)
// Events -> Signals -> Features -> Evidence -> Trust Dimensions -> Decision Intelligence -> Recommendation

export type ReliabilityLevel = "A+" | "A" | "B+" | "B" | "C" | "D";

export type SeverityLevel = "low" | "medium" | "high";

export type ConfidenceBand = "very-high" | "high" | "moderate" | "low" | "very-low";

export type RecommendationAction =
  | "proceed-normally"
  | "continue-monitoring"
  | "additional-evidence"
  | "manual-review"
  | "high-risk-investigation";

export interface TrustDNA {
  behavioralConsistency: number; // Trust DNA dimension 1
  attentionStability: number; // 2
  interactionNaturalness: number; // 3
  contextIntegrity: number; // 4
  adaptiveResponsiveness: number; // 5
  sessionAuthenticity: number; // 6 — weighted synthesis
}

export interface LiveSignal {
  id: string;
  label: string;
  value: number; // normalized 0-100
  unit?: string;
  trend: "up" | "down" | "flat";
  updatedAt: string;
}

export interface EvidenceItem {
  id: string;
  index: number;
  category:
    | "Behavior Consistency"
    | "Interaction Naturalness"
    | "Attention Stability"
    | "Context Integrity"
    | "Adaptive Responsiveness";
  title: string;
  observation: string;
  supportingSignals: string[];
  confidence: number; // evidence confidence, distinct from decision confidence
  severity: SeverityLevel;
  timestamp: string;
}

export interface TimelineEvent {
  id: string;
  type:
    | "session-started"
    | "focus-lost"
    | "focus-regained"
    | "behavior-shift"
    | "evidence-generated"
    | "recommendation-updated"
    | "session-ended";
  label: string;
  detail?: string;
  timestamp: string;
  severity?: SeverityLevel;
}

export interface Recommendation {
  action: RecommendationAction;
  label: string;
  reasons: string[];
  confidence: number; // decision confidence, calibrated
  confidenceBand: ConfidenceBand;
  generatedAt: string;
}

export interface SessionSummary {
  id: string;
  candidateName: string;
  observerName: string;
  position: string;
  department?: string;
  interviewType: string;
  startedAt: string;
  endedAt?: string;
  status: "scheduled" | "live" | "completed";
  trustDNA: TrustDNA;
  decisionConfidence: number;
  recommendation: Recommendation["action"];
  evidenceCount: number;
  durationSeconds: number;
}

export interface SignalTaxonomyItem {
  id: string;
  name: string;
  category: "Interaction" | "Temporal" | "Context" | "Navigation" | "Behavioral" | "System";
  purpose: string;
  trustDimension: keyof TrustDNA;
  reliability: ReliabilityLevel;
  privacy: "Low" | "Medium" | "High";
  mvpStatus: "Included" | "Future";
}
