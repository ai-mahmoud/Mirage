import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import type { EvidenceItem, LiveSignal, Recommendation, TimelineEvent, TrustDNA } from "@/types/domain";
import { endSession as apiEndSession, getTrustStatus } from "@/lib/api-client";
import { deriveTimelineFromEvidence, mapEvidenceList, mapRecommendation, mapTrustDna } from "@/lib/session-mappers";
import { useEventTracker } from "./event-tracker";

const POLL_INTERVAL_MS = 1000;

const EMPTY_TRUST_DNA: TrustDNA = {
  behavioralConsistency: 75,
  attentionStability: 75,
  interactionNaturalness: 75,
  contextIntegrity: 75,
  adaptiveResponsiveness: 75,
  sessionAuthenticity: 75,
};

// Replaces the old client-simulated version: real browser events are
// captured (useEventTracker) and posted to the backend, and Trust DNA /
// evidence / recommendation are polled from it every second — matching
// CLAUDE.md's "signal stream every second" / "<1s dashboard latency".
export function useLiveSession(sessionId: string) {
  const [elapsed, setElapsed] = React.useState(0);
  const [startedAt] = React.useState(() => Date.now());
  const [running, setRunning] = React.useState(true);

  useEventTracker(sessionId, running);

  const { data } = useQuery({
    queryKey: ["session-trust", sessionId],
    queryFn: () => getTrustStatus(sessionId),
    refetchInterval: running ? POLL_INTERVAL_MS : false,
    enabled: !!sessionId,
  });

  React.useEffect(() => {
    if (!running) return;
    const timer = setInterval(() => setElapsed((s) => s + 1), 1000);
    return () => clearInterval(timer);
  }, [running]);

  const trustDNA: TrustDNA = data ? mapTrustDna(data.trustDna) : EMPTY_TRUST_DNA;
  const evidence: EvidenceItem[] = data ? mapEvidenceList(data.evidence) : [];
  const recommendation: Recommendation = data
    ? mapRecommendation(data.recommendation, data.recommendationConfidence)
    : {
        action: "continue-monitoring",
        label: "Insufficient Evidence",
        reasons: ["Waiting for the first behavioral signals to arrive."],
        confidence: 0,
        confidenceBand: "very-low",
        generatedAt: new Date().toISOString(),
      };
  // ai/'s SessionSnapshot doesn't expose a per-signal live feed on this
  // endpoint (only evidence + Trust DNA) — the "Live Signals" panel is fed
  // from the same evidence-confidence trend as a lightweight stand-in.
  const signals: LiveSignal[] = React.useMemo<LiveSignal[]>(() => {
    if (!data) return [];
    return [
      { id: "evidence-confidence", label: "Evidence Confidence", value: Math.round(data.evidenceConfidence * 100), trend: "flat", updatedAt: new Date().toISOString() },
      { id: "recommendation-confidence", label: "Recommendation Confidence", value: Math.round(data.recommendationConfidence * 100), trend: "flat", updatedAt: new Date().toISOString() },
    ];
  }, [data]);

  const timeline: TimelineEvent[] = React.useMemo(
    () => deriveTimelineFromEvidence(evidence, new Date(startedAt).toISOString()),
    [evidence, startedAt]
  );

  const decisionConfidence = recommendation.confidence;

  const endSession = React.useCallback(async () => {
    setRunning(false);
    if (sessionId) {
      await apiEndSession(sessionId).catch(() => {
        // Report screen will still show whatever the last successful poll had.
      });
    }
  }, [sessionId]);

  return {
    elapsed,
    trustDNA,
    signals,
    evidence,
    timeline,
    recommendation,
    decisionConfidence,
    running,
    setRunning,
    endSession,
  };
}
