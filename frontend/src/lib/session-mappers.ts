// Pure functions mapping backend wire types (src/types/api.ts) onto the
// app's domain model (src/types/domain.ts). No React, no fetching — every
// function here is a plain data transformation, unit-testable in isolation.
import { bandFromScore } from "@/lib/confidence";
import type {
  EvidenceOutRaw,
  RecommendationOutRaw,
  SessionResponseRaw,
  TrustDnaOutRaw,
} from "@/types/api";
import type {
  EvidenceItem,
  Recommendation,
  RecommendationAction,
  SessionSummary,
  TimelineEvent,
  TrustDNA,
} from "@/types/domain";

const DIMENSION_KEY_BY_ID: Record<string, keyof TrustDNA> = {
  behavioral_consistency: "behavioralConsistency",
  interaction_naturalness: "interactionNaturalness",
  attention_stability: "attentionStability",
  context_integrity: "contextIntegrity",
  adaptive_responsiveness: "adaptiveResponsiveness",
  session_authenticity: "sessionAuthenticity",
};

export function mapTrustDna(raw: TrustDnaOutRaw): TrustDNA {
  const dna: TrustDNA = {
    behavioralConsistency: 0,
    attentionStability: 0,
    interactionNaturalness: 0,
    contextIntegrity: 0,
    adaptiveResponsiveness: 0,
    sessionAuthenticity: 0,
  };
  for (const dim of raw.dimensions) {
    const key = DIMENSION_KEY_BY_ID[dim.id];
    if (key) dna[key] = dim.score;
  }
  return dna;
}

// ai/'s 4 statuses map onto the frontend's richer 5-action vocabulary by
// name/tone correspondence (see RECOMMENDATION_META in lib/confidence.ts).
// ai/'s engine never emits anything requiring "high-risk-investigation" —
// its most severe state is manual_review_recommended, by design (the
// product's conservative-language constitution).
const ACTION_BY_STATUS: Record<string, RecommendationAction> = {
  continue_monitoring: "proceed-normally",
  evidence_insufficient: "continue-monitoring",
  additional_observation_recommended: "additional-evidence",
  manual_review_recommended: "manual-review",
};

export function mapAiStatusToAction(status: string): RecommendationAction {
  return ACTION_BY_STATUS[status] ?? "continue-monitoring";
}

// ai/'s evidence-reasoning only ever produces 3 category buckets; "Context
// Integrity" and "Adaptive Responsiveness" are valid EvidenceItem
// categories the frontend defines but ai/ never populates.
const EVIDENCE_CATEGORY_BY_AI_CATEGORY: Record<string, EvidenceItem["category"]> = {
  interaction_naturalness: "Interaction Naturalness",
  attention: "Attention Stability",
  consistency: "Behavior Consistency",
};

export function mapEvidenceCategory(aiCategory: string): EvidenceItem["category"] {
  return EVIDENCE_CATEGORY_BY_AI_CATEGORY[aiCategory] ?? "Behavior Consistency";
}

export function mapEvidenceList(raw: EvidenceOutRaw[]): EvidenceItem[] {
  const newestFirst = [...raw].sort(
    (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  );
  return newestFirst.map((card, i) => ({
    id: card.id,
    index: newestFirst.length - i,
    category: mapEvidenceCategory(card.category),
    title: card.title,
    observation: card.description,
    supportingSignals: card.supportingSignals,
    confidence: Math.round(card.confidence * 100),
    severity: card.severity === "info" ? "low" : card.severity,
    timestamp: card.timestamp,
  }));
}

export function mapRecommendation(raw: RecommendationOutRaw, recommendationConfidence: number): Recommendation {
  const confidence = Math.round(recommendationConfidence * 100);
  return {
    action: mapAiStatusToAction(raw.status),
    label: raw.label,
    reasons: raw.reasons,
    confidence,
    confidenceBand: bandFromScore(confidence),
    generatedAt: new Date().toISOString(),
  };
}

export function mapSessionSummary(raw: SessionResponseRaw): SessionSummary {
  const startedAtMs = new Date(raw.createdAt).getTime();
  const endedAtMs = raw.endedAt ? new Date(raw.endedAt).getTime() : Date.now();
  return {
    id: raw.sessionId,
    candidateName: raw.candidateName,
    observerName: raw.observerName ?? "Interviewer",
    position: raw.position ?? "—",
    department: raw.department ?? undefined,
    interviewType: raw.interviewType,
    startedAt: raw.createdAt,
    endedAt: raw.endedAt ?? undefined,
    status: raw.status === "ended" ? "completed" : "live",
    trustDNA: mapTrustDna({ dimensions: raw.trustDimensions, overall: raw.trustOverall }),
    decisionConfidence: Math.round(raw.recommendationConfidence * 100),
    recommendation: mapAiStatusToAction(raw.recommendationStatus),
    evidenceCount: raw.evidenceCount,
    durationSeconds: Math.max(0, Math.round((endedAtMs - startedAtMs) / 1000)),
  };
}

// ai/'s live TrustStatusResponse carries no session-wide timeline (only
// SessionReportOut does, and fetching that finalizes the ai/ session — not
// safe to call on an in-progress interview). Synthesized here instead, from
// the same evidence list every live-data consumer already has.
export function deriveTimelineFromEvidence(evidence: EvidenceItem[], startedAt?: string): TimelineEvent[] {
  const events: TimelineEvent[] = [];
  if (startedAt) {
    events.push({ id: "start", type: "session-started", label: "Session started", timestamp: startedAt });
  }
  for (const e of evidence) {
    events.push({
      id: `evidence-${e.id}`,
      type: "evidence-generated",
      label: e.title,
      detail: e.observation,
      timestamp: e.timestamp,
      severity: e.severity,
    });
  }
  return events.sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
}

export interface ActivityItem {
  id: string;
  label: string;
  detail: string;
  timestamp: string;
}

// Synthesizes a Dashboard activity feed purely from the sessions list —
// no separate cross-session event log exists on the backend, and building
// one would be exactly the kind of historical-analytics infrastructure
// CLAUDE.md calls out of scope for the MVP.
export function deriveActivityFeed(sessions: SessionSummary[], limit = 8): ActivityItem[] {
  const items: ActivityItem[] = [];
  for (const s of sessions) {
    items.push({
      id: `${s.id}-started`,
      label: `Session started — ${s.candidateName}`,
      detail: s.interviewType,
      timestamp: s.startedAt,
    });
    if (s.endedAt) {
      items.push({
        id: `${s.id}-ended`,
        label: `Session ended — ${s.candidateName}`,
        detail: `Final Trust DNA ${Math.round(s.trustDNA.sessionAuthenticity)}`,
        timestamp: s.endedAt,
      });
    }
  }
  return items
    .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
    .slice(0, limit);
}
