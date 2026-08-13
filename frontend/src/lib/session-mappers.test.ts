import { describe, expect, it } from "vitest";
import {
  deriveActivityFeed,
  deriveTimelineFromEvidence,
  mapAiStatusToAction,
  mapEvidenceCategory,
  mapEvidenceList,
  mapRecommendation,
  mapSessionSummary,
  mapTrustDna,
} from "./session-mappers";
import type { EvidenceOutRaw, RecommendationOutRaw, SessionResponseRaw, TrustDnaOutRaw } from "@/types/api";

describe("mapTrustDna", () => {
  it("maps every known dimension id onto the domain shape", () => {
    const raw: TrustDnaOutRaw = {
      overall: 70,
      dimensions: [
        { id: "behavioral_consistency", label: "x", score: 10, trend: "stable" },
        { id: "interaction_naturalness", label: "x", score: 20, trend: "up" },
        { id: "attention_stability", label: "x", score: 30, trend: "down" },
        { id: "context_integrity", label: "x", score: 40, trend: "stable" },
        { id: "adaptive_responsiveness", label: "x", score: 50, trend: "stable" },
        { id: "session_authenticity", label: "x", score: 60, trend: "stable" },
      ],
    };
    expect(mapTrustDna(raw)).toEqual({
      behavioralConsistency: 10,
      interactionNaturalness: 20,
      attentionStability: 30,
      contextIntegrity: 40,
      adaptiveResponsiveness: 50,
      sessionAuthenticity: 60,
    });
  });

  it("leaves a dimension at 0 when ai/ didn't report it (missing-data policy)", () => {
    const raw: TrustDnaOutRaw = { overall: 0, dimensions: [{ id: "behavioral_consistency", label: "x", score: 99, trend: "stable" }] };
    expect(mapTrustDna(raw).interactionNaturalness).toBe(0);
  });

  it("ignores an unknown dimension id rather than throwing", () => {
    const raw: TrustDnaOutRaw = { overall: 0, dimensions: [{ id: "made_up", label: "x", score: 99, trend: "stable" }] };
    expect(() => mapTrustDna(raw)).not.toThrow();
  });
});

describe("mapAiStatusToAction", () => {
  it("maps every known ai/ status to its frontend action", () => {
    expect(mapAiStatusToAction("continue_monitoring")).toBe("proceed-normally");
    expect(mapAiStatusToAction("evidence_insufficient")).toBe("continue-monitoring");
    expect(mapAiStatusToAction("additional_observation_recommended")).toBe("additional-evidence");
    expect(mapAiStatusToAction("manual_review_recommended")).toBe("manual-review");
  });

  it("falls back to continue-monitoring for an unrecognized status", () => {
    expect(mapAiStatusToAction("something_new")).toBe("continue-monitoring");
  });
});

describe("mapEvidenceCategory", () => {
  it("maps every known ai/ category", () => {
    expect(mapEvidenceCategory("interaction_naturalness")).toBe("Interaction Naturalness");
    expect(mapEvidenceCategory("attention")).toBe("Attention Stability");
    expect(mapEvidenceCategory("consistency")).toBe("Behavior Consistency");
  });

  it("falls back to Behavior Consistency for an unrecognized category", () => {
    expect(mapEvidenceCategory("unknown")).toBe("Behavior Consistency");
  });
});

describe("mapEvidenceList", () => {
  const card = (overrides: Partial<EvidenceOutRaw>): EvidenceOutRaw => ({
    id: "EV-1",
    category: "attention",
    title: "t",
    description: "d",
    severity: "medium",
    polarity: "reduces_trust",
    confidence: 0.5,
    timestamp: "2026-01-01T00:00:00Z",
    supportingSignals: [],
    ...overrides,
  });

  it("sorts newest first and assigns a descending index", () => {
    const raw = [
      card({ id: "old", timestamp: "2026-01-01T00:00:00Z" }),
      card({ id: "new", timestamp: "2026-01-02T00:00:00Z" }),
    ];
    const mapped = mapEvidenceList(raw);
    expect(mapped.map((e) => e.id)).toEqual(["new", "old"]);
    expect(mapped[0].index).toBe(2);
    expect(mapped[1].index).toBe(1);
  });

  it("converts confidence to a 0-100 integer", () => {
    const [mapped] = mapEvidenceList([card({ confidence: 0.73 })]);
    expect(mapped.confidence).toBe(73);
  });

  it('remaps "info" severity to "low", passes through everything else', () => {
    expect(mapEvidenceList([card({ severity: "info" })])[0].severity).toBe("low");
    expect(mapEvidenceList([card({ severity: "high" })])[0].severity).toBe("high");
  });
});

describe("mapRecommendation", () => {
  it("converts recommendationConfidence (0-1) to a 0-100 band", () => {
    const raw: RecommendationOutRaw = {
      status: "manual_review_recommended",
      label: "Manual Review Recommended",
      reasons: ["x"],
      suggestedAction: "review",
      humanReviewRequired: true,
    };
    const mapped = mapRecommendation(raw, 0.85);
    expect(mapped.confidence).toBe(85);
    expect(mapped.confidenceBand).toBe("high");
    expect(mapped.action).toBe("manual-review");
    expect(mapped.reasons).toEqual(["x"]);
  });
});

describe("mapSessionSummary", () => {
  const base: SessionResponseRaw = {
    sessionId: "s1",
    candidateName: "Ada",
    interviewType: "Technical Interview",
    position: null,
    department: null,
    observerName: null,
    status: "ended",
    createdAt: "2026-01-01T00:00:00.000Z",
    endedAt: "2026-01-01T00:10:00.000Z",
    trustOverall: 70,
    trustDimensions: [],
    evidenceConfidence: 0.5,
    recommendationConfidence: 0.5,
    recommendationStatus: "continue_monitoring",
    recommendationLabel: "Continue Monitoring",
    evidenceCount: 3,
  };

  it("maps ended status and computes duration from created/ended timestamps", () => {
    const mapped = mapSessionSummary(base);
    expect(mapped.status).toBe("completed");
    expect(mapped.durationSeconds).toBe(600);
    expect(mapped.evidenceCount).toBe(3);
  });

  it('maps "active" status to "live" and applies sensible defaults for null fields', () => {
    const mapped = mapSessionSummary({ ...base, status: "active", endedAt: null, observerName: null, position: null });
    expect(mapped.status).toBe("live");
    expect(mapped.observerName).toBe("Interviewer");
    expect(mapped.position).toBe("—");
    expect(mapped.endedAt).toBeUndefined();
  });
});

describe("deriveTimelineFromEvidence", () => {
  it("includes a session-started entry when startedAt is given, sorted chronologically", () => {
    const evidence = [
      { id: "1", index: 1, category: "Behavior Consistency" as const, title: "Later", observation: "", supportingSignals: [], confidence: 90, severity: "low" as const, timestamp: "2026-01-01T00:02:00Z" },
      { id: "2", index: 2, category: "Behavior Consistency" as const, title: "Earlier", observation: "", supportingSignals: [], confidence: 90, severity: "low" as const, timestamp: "2026-01-01T00:01:00Z" },
    ];
    const timeline = deriveTimelineFromEvidence(evidence, "2026-01-01T00:00:00Z");
    expect(timeline.map((e) => e.label)).toEqual(["Session started", "Earlier", "Later"]);
  });

  it("omits the session-started entry when no startedAt is given", () => {
    expect(deriveTimelineFromEvidence([])).toEqual([]);
  });
});

describe("deriveActivityFeed", () => {
  it("emits a started entry and, only if ended, an ended entry, newest first", () => {
    const sessions = [
      mapSessionSummary({
        sessionId: "s1",
        candidateName: "Ada",
        interviewType: "Technical Interview",
        position: null,
        department: null,
        observerName: null,
        status: "active",
        createdAt: "2026-01-01T00:00:00Z",
        endedAt: null,
        trustOverall: 70,
        trustDimensions: [],
        evidenceConfidence: 0.5,
        recommendationConfidence: 0.5,
        recommendationStatus: "continue_monitoring",
        recommendationLabel: "Continue Monitoring",
        evidenceCount: 0,
      }),
      mapSessionSummary({
        sessionId: "s2",
        candidateName: "Bo",
        interviewType: "Technical Interview",
        position: null,
        department: null,
        observerName: null,
        status: "ended",
        createdAt: "2026-01-02T00:00:00Z",
        endedAt: "2026-01-02T00:05:00Z",
        trustOverall: 70,
        trustDimensions: [],
        evidenceConfidence: 0.5,
        recommendationConfidence: 0.5,
        recommendationStatus: "continue_monitoring",
        recommendationLabel: "Continue Monitoring",
        evidenceCount: 0,
      }),
    ];
    const feed = deriveActivityFeed(sessions);
    expect(feed.map((i) => i.label)).toEqual([
      "Session ended — Bo",
      "Session started — Bo",
      "Session started — Ada",
    ]);
  });

  it("respects the limit", () => {
    const sessions = Array.from({ length: 5 }, (_, i) =>
      mapSessionSummary({
        sessionId: `s${i}`,
        candidateName: `C${i}`,
        interviewType: "Technical Interview",
        position: null,
        department: null,
        observerName: null,
        status: "active",
        createdAt: `2026-01-0${i + 1}T00:00:00Z`,
        endedAt: null,
        trustOverall: 70,
        trustDimensions: [],
        evidenceConfidence: 0.5,
        recommendationConfidence: 0.5,
        recommendationStatus: "continue_monitoring",
        recommendationLabel: "Continue Monitoring",
        evidenceCount: 0,
      })
    );
    expect(deriveActivityFeed(sessions, 2)).toHaveLength(2);
  });
});
