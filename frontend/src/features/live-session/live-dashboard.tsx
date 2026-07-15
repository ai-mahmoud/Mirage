import { Pause, Play, Square, Timer } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { TrustDNACard } from "@/components/dashboard/trust-dna-card";
import { EvidenceFeed } from "@/components/dashboard/evidence-feed";
import { BehaviorTimeline } from "@/components/dashboard/behavior-timeline";
import { LiveSignalStream, PrivacyCard } from "@/components/dashboard/privacy-signals";
import { DecisionConfidenceCard, RecommendationPanel } from "@/components/dashboard/recommendation-panel";
import { formatDuration } from "@/lib/utils";
import type { CreateSessionResult } from "./create-session-form";
import { useLiveSession } from "./use-live-session";

export function LiveDashboard({ session, onEnd }: { session: CreateSessionResult; onEnd: () => void }) {
  const { elapsed, trustDNA, signals, evidence, timeline, recommendation, decisionConfidence, running, setRunning, endSession } =
    useLiveSession(session.sessionId);

  return (
    <div className="space-y-6">
      {/* Session header */}
      <Card>
        <CardContent className="flex flex-wrap items-center justify-between gap-4 p-5">
          <div className="flex flex-wrap items-center gap-x-8 gap-y-2">
            <div>
              <p className="text-xs text-charcoal-500">Candidate</p>
              <p className="text-sm font-semibold text-charcoal-800">{session.candidateName || "Candidate A"}</p>
            </div>
            <div>
              <p className="text-xs text-charcoal-500">Observer</p>
              <p className="text-sm font-semibold text-charcoal-800">{session.observerName}</p>
            </div>
            <div>
              <p className="text-xs text-charcoal-500">Role</p>
              <p className="text-sm font-semibold text-charcoal-800">{session.position || "—"}</p>
            </div>
            <div>
              <p className="text-xs text-charcoal-500">Department</p>
              <p className="text-sm font-semibold text-charcoal-800">{session.department || "—"}</p>
            </div>
            <div className="flex items-center gap-2">
              <Timer className="size-4 text-charcoal-400" />
              <span className="tabular text-sm font-semibold text-charcoal-800">{formatDuration(elapsed)}</span>
            </div>
            <Badge tone={running ? "success" : "neutral"} dot>
              {running ? "Live" : "Paused"}
            </Badge>
          </div>
          <div className="flex gap-2">
            <Button variant="secondary" size="sm" className="gap-1.5" onClick={() => setRunning((r) => !r)}>
              {running ? <Pause className="size-3.5" /> : <Play className="size-3.5" />}
              {running ? "Pause" : "Resume"}
            </Button>
            <Button
              variant="danger"
              size="sm"
              className="gap-1.5"
              onClick={async () => {
                await endSession();
                onEnd();
              }}
            >
              <Square className="size-3.5" /> End Session
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Main grid: Trust DNA | Timeline | Evidence */}
      <div className="grid gap-6 xl:grid-cols-3">
        <TrustDNACard trustDNA={trustDNA} />
        <BehaviorTimeline events={timeline} />
        <EvidenceFeed items={evidence} />
      </div>

      {/* Bottom grid: Live signals | Recommendation | Privacy */}
      <div className="grid gap-6 xl:grid-cols-3">
        <LiveSignalStream signals={signals} />
        <div className="space-y-6 xl:col-span-2">
          <div className="grid gap-6 sm:grid-cols-2">
            <DecisionConfidenceCard confidence={decisionConfidence} />
            <PrivacyCard />
          </div>
          <RecommendationPanel recommendation={recommendation} onGenerateReport={onEnd} />
        </div>
      </div>
    </div>
  );
}
