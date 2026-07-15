// DEMO DATA — Hackathon MVP static/simulated dataset.
// Clearly marked as demo data per MVP Bible §9 (In Scope) and Principle 5 (Simplicity).
// No real candidate data is used anywhere in this file.

import type {
  EvidenceItem,
  LiveSignal,
  Recommendation,
  SessionSummary,
  SignalTaxonomyItem,
  TimelineEvent,
  TrustDNA,
} from "@/types/domain";

export const DEMO_TRUST_DNA: TrustDNA = {
  behavioralConsistency: 91,
  attentionStability: 88,
  interactionNaturalness: 84,
  contextIntegrity: 95,
  adaptiveResponsiveness: 90,
  sessionAuthenticity: 89,
};

export const DEMO_TRUST_DNA_DEGRADED: TrustDNA = {
  behavioralConsistency: 62,
  attentionStability: 71,
  interactionNaturalness: 48,
  contextIntegrity: 83,
  adaptiveResponsiveness: 66,
  sessionAuthenticity: 58,
};

export const TRUST_DNA_LABELS: Record<keyof TrustDNA, { label: string; description: string }> = {
  behavioralConsistency: {
    label: "Behavioral Consistency",
    description: "Stability of interaction patterns over the session.",
  },
  attentionStability: {
    label: "Attention Stability",
    description: "Continuity of engagement and focus recovery.",
  },
  interactionNaturalness: {
    label: "Interaction Naturalness",
    description: "Variability expected from genuine human behavior.",
  },
  contextIntegrity: {
    label: "Context Integrity",
    description: "Environmental and session coherence.",
  },
  adaptiveResponsiveness: {
    label: "Adaptive Responsiveness",
    description: "Natural response to changing conditions.",
  },
  sessionAuthenticity: {
    label: "Session Authenticity",
    description: "Weighted synthesis of all behavioral dimensions.",
  },
};

export const DEMO_LIVE_SIGNALS: LiveSignal[] = [
  { id: "sig-mouse", label: "Mouse Activity", value: 78, unit: "entropy", trend: "flat", updatedAt: new Date().toISOString() },
  { id: "sig-keyboard", label: "Keyboard Rhythm", value: 85, unit: "consistency", trend: "up", updatedAt: new Date().toISOString() },
  { id: "sig-focus", label: "Focus Events", value: 96, unit: "stability", trend: "flat", updatedAt: new Date().toISOString() },
  { id: "sig-idle", label: "Idle Recovery", value: 90, unit: "smoothness", trend: "up", updatedAt: new Date().toISOString() },
  { id: "sig-window", label: "Window Activity", value: 93, unit: "coherence", trend: "flat", updatedAt: new Date().toISOString() },
  { id: "sig-density", label: "Interaction Frequency", value: 71, unit: "events/min", trend: "down", updatedAt: new Date().toISOString() },
];

export const DEMO_EVIDENCE: EvidenceItem[] = [
  {
    id: "ev-014",
    index: 14,
    category: "Behavior Consistency",
    title: "Behavioral Entropy Decreased",
    observation: "Interaction timing became significantly repetitive during the last 4 minutes.",
    supportingSignals: ["Reduced timing variance", "Increased repetitive mouse trajectory", "Stable idle recovery pattern"],
    confidence: 94,
    severity: "medium",
    timestamp: new Date(Date.now() - 2 * 60_000).toISOString(),
  },
  {
    id: "ev-013",
    index: 13,
    category: "Interaction Naturalness",
    title: "Low Interaction Diversity",
    observation: "Cursor movement showed reduced path curvature compared to session baseline.",
    supportingSignals: ["Path curvature below threshold", "Constant velocity segments"],
    confidence: 87,
    severity: "medium",
    timestamp: new Date(Date.now() - 4 * 60_000).toISOString(),
  },
  {
    id: "ev-012",
    index: 12,
    category: "Attention Stability",
    title: "Consistent Idle Recovery",
    observation: "Activity resumed smoothly after each idle period, consistent with natural attention patterns.",
    supportingSignals: ["Recovery delay within expected range", "No abrupt behavioral jumps"],
    confidence: 91,
    severity: "low",
    timestamp: new Date(Date.now() - 6 * 60_000).toISOString(),
  },
  {
    id: "ev-011",
    index: 11,
    category: "Context Integrity",
    title: "Abnormal Timing",
    observation: "Response latency briefly diverged from the established session rhythm.",
    supportingSignals: ["Latency variance spike", "Single occurrence, not sustained"],
    confidence: 76,
    severity: "low",
    timestamp: new Date(Date.now() - 9 * 60_000).toISOString(),
  },
  {
    id: "ev-010",
    index: 10,
    category: "Behavior Consistency",
    title: "Stable Typing Cadence Established",
    observation: "Typing rhythm formed a consistent baseline across the opening segment of the session.",
    supportingSignals: ["Inter-key delay variance low", "Natural burst pattern detected"],
    confidence: 96,
    severity: "low",
    timestamp: new Date(Date.now() - 14 * 60_000).toISOString(),
  },
];

export const DEMO_TIMELINE: TimelineEvent[] = [
  { id: "tl-1", type: "session-started", label: "Session Started", timestamp: new Date(Date.now() - 15 * 60_000).toISOString() },
  { id: "tl-2", type: "focus-lost", label: "Focus Lost", detail: "Window switched for 4s", timestamp: new Date(Date.now() - 12 * 60_000).toISOString(), severity: "low" },
  { id: "tl-3", type: "focus-regained", label: "Focus Regained", timestamp: new Date(Date.now() - 11 * 60_000).toISOString() },
  { id: "tl-4", type: "evidence-generated", label: "Evidence Generated", detail: "Abnormal Timing (#11)", timestamp: new Date(Date.now() - 9 * 60_000).toISOString(), severity: "low" },
  { id: "tl-5", type: "behavior-shift", label: "Behavioral Pattern Changed", detail: "Repetitive interaction detected", timestamp: new Date(Date.now() - 4 * 60_000).toISOString(), severity: "medium" },
  { id: "tl-6", type: "evidence-generated", label: "Evidence Generated", detail: "Behavioral Entropy Decreased (#14)", timestamp: new Date(Date.now() - 2 * 60_000).toISOString(), severity: "medium" },
  { id: "tl-7", type: "recommendation-updated", label: "Recommendation Updated", detail: "Manual Review Recommended", timestamp: new Date(Date.now() - 1 * 60_000).toISOString(), severity: "medium" },
];

export const DEMO_RECOMMENDATION: Recommendation = {
  action: "manual-review",
  label: "Manual Review Recommended",
  reasons: [
    "Behavior consistency decreased below expected threshold.",
    "Interaction rhythm became highly repetitive.",
    "Evidence confidence increased while behavioral confidence reduced.",
  ],
  confidence: 71,
  confidenceBand: "moderate",
  generatedAt: new Date(Date.now() - 1 * 60_000).toISOString(),
};

export const DEMO_SESSIONS: SessionSummary[] = [
  {
    id: "SES-10231",
    candidateName: "Candidate A",
    observerName: "J. Whitfield",
    position: "Senior Backend Engineer",
    department: "Engineering",
    interviewType: "Technical Interview",
    startedAt: new Date(Date.now() - 15 * 60_000).toISOString(),
    status: "live",
    trustDNA: DEMO_TRUST_DNA_DEGRADED,
    decisionConfidence: 71,
    recommendation: "manual-review",
    evidenceCount: 14,
    durationSeconds: 15 * 60,
  },
  {
    id: "SES-10228",
    candidateName: "Candidate B",
    observerName: "R. Alonso",
    position: "Product Designer",
    department: "Design",
    interviewType: "Portfolio Review",
    startedAt: new Date(Date.now() - 3 * 60 * 60_000).toISOString(),
    endedAt: new Date(Date.now() - 3 * 60 * 60_000 + 28 * 60_000).toISOString(),
    status: "completed",
    trustDNA: DEMO_TRUST_DNA,
    decisionConfidence: 94,
    recommendation: "proceed-normally",
    evidenceCount: 6,
    durationSeconds: 28 * 60,
  },
  {
    id: "SES-10219",
    candidateName: "Candidate C",
    observerName: "J. Whitfield",
    position: "Data Analyst",
    department: "Analytics",
    interviewType: "Screening Call",
    startedAt: new Date(Date.now() - 26 * 60 * 60_000).toISOString(),
    endedAt: new Date(Date.now() - 26 * 60 * 60_000 + 19 * 60_000).toISOString(),
    status: "completed",
    trustDNA: { ...DEMO_TRUST_DNA, interactionNaturalness: 79, sessionAuthenticity: 82 },
    decisionConfidence: 86,
    recommendation: "additional-evidence",
    evidenceCount: 9,
    durationSeconds: 19 * 60,
  },
];

export const SIGNAL_TAXONOMY: SignalTaxonomyItem[] = [
  { id: "SIG-001", name: "Cursor Velocity", category: "Interaction", purpose: "Measure movement speed variation.", trustDimension: "interactionNaturalness", reliability: "A", privacy: "Low", mvpStatus: "Included" },
  { id: "SIG-002", name: "Cursor Entropy", category: "Interaction", purpose: "Measure diversity of cursor movement.", trustDimension: "interactionNaturalness", reliability: "A+", privacy: "Low", mvpStatus: "Included" },
  { id: "SIG-003", name: "Path Curvature", category: "Interaction", purpose: "Evaluate geometric complexity of movement.", trustDimension: "interactionNaturalness", reliability: "A", privacy: "Low", mvpStatus: "Included" },
  { id: "SIG-004", name: "Click Rhythm", category: "Interaction", purpose: "Evaluate click timing diversity.", trustDimension: "behavioralConsistency", reliability: "B+", privacy: "Low", mvpStatus: "Included" },
  { id: "SIG-005", name: "Typing Rhythm", category: "Behavioral", purpose: "Measure natural typing cadence.", trustDimension: "behavioralConsistency", reliability: "A+", privacy: "Medium", mvpStatus: "Included" },
  { id: "SIG-006", name: "Pause Distribution", category: "Temporal", purpose: "Measure cognitive pause behavior.", trustDimension: "attentionStability", reliability: "A", privacy: "Low", mvpStatus: "Included" },
  { id: "SIG-007", name: "Idle Recovery", category: "Behavioral", purpose: "Evaluate how naturally activity resumes.", trustDimension: "attentionStability", reliability: "A", privacy: "Low", mvpStatus: "Included" },
  { id: "SIG-008", name: "Window Focus Stability", category: "Navigation", purpose: "Measure application focus consistency.", trustDimension: "contextIntegrity", reliability: "B", privacy: "Low", mvpStatus: "Included" },
  { id: "SIG-009", name: "Browser Visibility", category: "Navigation", purpose: "Observe background execution.", trustDimension: "contextIntegrity", reliability: "C", privacy: "Low", mvpStatus: "Included" },
  { id: "SIG-010", name: "Response Latency", category: "Temporal", purpose: "Measure reaction timing.", trustDimension: "adaptiveResponsiveness", reliability: "A", privacy: "Low", mvpStatus: "Included" },
  { id: "SIG-011", name: "Interaction Density", category: "System", purpose: "Measure interaction intensity.", trustDimension: "sessionAuthenticity" as const, reliability: "B+", privacy: "Low", mvpStatus: "Included" },
  { id: "SIG-012", name: "Scroll Dynamics", category: "Interaction", purpose: "Measure natural scrolling behavior.", trustDimension: "interactionNaturalness", reliability: "B", privacy: "Low", mvpStatus: "Included" },
];

export const KPI_SUMMARY = {
  systemHealth: "Operational",
  behaviorEngineStatus: "Running",
  todaysSessions: 7,
  averageDecisionConfidence: 88,
};

export const ACTIVITY_FEED = [
  { id: "a1", label: "Session Started", detail: "Candidate A · Senior Backend Engineer", timestamp: new Date(Date.now() - 15 * 60_000).toISOString() },
  { id: "a2", label: "Evidence Generated", detail: "Behavioral Entropy Decreased (#14)", timestamp: new Date(Date.now() - 2 * 60_000).toISOString() },
  { id: "a3", label: "Risk Updated", detail: "Candidate A moved to Moderate confidence", timestamp: new Date(Date.now() - 1 * 60_000).toISOString() },
  { id: "a4", label: "Recommendation Changed", detail: "Manual Review Recommended", timestamp: new Date(Date.now() - 1 * 60_000).toISOString() },
  { id: "a5", label: "Session Completed", detail: "Candidate B · Product Designer", timestamp: new Date(Date.now() - 3 * 60 * 60_000).toISOString() },
];

export const TRUST_DISTRIBUTION = [
  { band: "Very High", count: 12 },
  { band: "High", count: 21 },
  { band: "Moderate", count: 9 },
  { band: "Low", count: 3 },
  { band: "Very Low", count: 1 },
];

export const DAILY_SESSIONS = [
  { day: "Mon", sessions: 5 },
  { day: "Tue", sessions: 8 },
  { day: "Wed", sessions: 6 },
  { day: "Thu", sessions: 9 },
  { day: "Fri", sessions: 7 },
  { day: "Sat", sessions: 2 },
  { day: "Sun", sessions: 1 },
];

export const CONFIDENCE_TREND = Array.from({ length: 15 }).map((_, i) => ({
  minute: i,
  confidence: Math.round(96 - i * 1.6 + (i % 3 === 0 ? 2 : 0) - (i > 10 ? (i - 10) * 1.2 : 0)),
}));
