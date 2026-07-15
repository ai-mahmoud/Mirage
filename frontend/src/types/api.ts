// Raw wire types — mirror backend/mirage_backend/schemas.py field-for-field
// (same camelCase JSON keys). Kept separate from ./domain.ts because the
// backend's shape and the app's domain model genuinely differ (see
// src/lib/session-mappers.ts for the mapping between them); these types
// exist so that difference is explicit rather than papered over.

export interface TrustDimensionOutRaw {
  id: string;
  label: string;
  score: number;
  trend: "up" | "down" | "stable";
}

export interface TrustDnaOutRaw {
  dimensions: TrustDimensionOutRaw[];
  overall: number;
}

export interface EvidenceOutRaw {
  id: string;
  category: string;
  title: string;
  description: string;
  severity: "info" | "low" | "medium" | "high";
  polarity: "supports_trust" | "reduces_trust" | "informational";
  confidence: number;
  timestamp: string; // ISO
  supportingSignals: string[];
}

export interface RecommendationOutRaw {
  status: string;
  label: string;
  reasons: string[];
  suggestedAction: string;
  humanReviewRequired: boolean;
}

export interface TrustStatusResponseRaw {
  sessionId: string;
  trustOverall: number;
  trustDna: TrustDnaOutRaw;
  evidenceConfidence: number;
  recommendationConfidence: number;
  currentRisk: string;
  recommendation: RecommendationOutRaw;
  evidence: EvidenceOutRaw[];
}

export interface SessionResponseRaw {
  sessionId: string;
  candidateName: string;
  interviewType: string;
  position: string | null;
  department: string | null;
  observerName: string | null;
  status: string;
  createdAt: string; // ISO
  endedAt: string | null;
  trustOverall: number;
  trustDimensions: TrustDimensionOutRaw[];
  evidenceConfidence: number;
  recommendationConfidence: number;
  recommendationStatus: string;
  recommendationLabel: string;
  evidenceCount: number;
}

export interface ConfidenceOutRaw {
  evidenceConfidence: number;
  recommendationConfidence: number;
  drivers: string[];
}

export interface TimelineEventOutRaw {
  t: number;
  type: string;
  label: string;
  detail: string | null;
}

export interface TrustDnaSampleOutRaw {
  t: number;
  overall: number;
}

export interface SessionReportRaw {
  sessionId: string;
  candidateName: string;
  observerName: string;
  position: string | null;
  department: string | null;
  interviewType: string | null;
  startedAt: number;
  endedAt: number;
  durationMs: number;
  generatedAt: number;
  executiveSummary: string;
  trustDna: TrustDnaOutRaw;
  trustDnaHistory: TrustDnaSampleOutRaw[];
  confidence: ConfidenceOutRaw;
  recommendation: RecommendationOutRaw;
  evidence: EvidenceOutRaw[];
  timeline: TimelineEventOutRaw[];
  privacyStatement: string[];
}

// --- outbound (frontend -> backend) ---

export type RawEventType =
  | "mouse_move"
  | "mouse_click"
  | "scroll"
  | "key_down"
  | "key_up"
  | "focus_gained"
  | "focus_lost"
  | "visibility_visible"
  | "visibility_hidden";

export interface RawEventOut {
  type: RawEventType;
  t: number;
  x?: number;
  y?: number;
  dy?: number;
}

export interface CreateSessionPayload {
  candidateName: string;
  interviewType: string;
  position?: string;
  department?: string;
  observerName?: string;
}
