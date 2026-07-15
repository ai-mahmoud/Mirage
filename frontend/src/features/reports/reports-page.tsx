import { motion } from "framer-motion";
import { useQuery } from "@tanstack/react-query";
import { Download, FileJson, FileSpreadsheet, FileText, ShieldCheck } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { TrustDNACard } from "@/components/dashboard/trust-dna-card";
import { NoActiveSession } from "@/components/shared/no-active-session";
import { getReport, reportPdfUrl } from "@/lib/api-client";
import { mapEvidenceList, mapRecommendation, mapTrustDna } from "@/lib/session-mappers";
import { useCurrentSession } from "@/contexts/session-context";
import { RECOMMENDATION_META, SEVERITY_META } from "@/lib/confidence";
import { formatDate } from "@/lib/utils";

export function ReportsPage() {
  const { currentSessionId } = useCurrentSession();
  const { data: report, isLoading } = useQuery({
    queryKey: ["report", currentSessionId],
    queryFn: () => getReport(currentSessionId as string),
    enabled: !!currentSessionId,
  });

  if (!currentSessionId) {
    return <NoActiveSession />;
  }

  if (isLoading || !report) {
    return <p className="text-sm text-charcoal-500">Loading report…</p>;
  }

  const trustDNA = mapTrustDna(report.trustDna);
  const evidence = mapEvidenceList(report.evidence);
  const recommendation = mapRecommendation(report.recommendation, report.confidence.recommendationConfidence);
  const meta = RECOMMENDATION_META[recommendation.action];

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-wrap items-center justify-between gap-4"
      >
        <div>
          <p className="text-xs text-charcoal-500">Session Report · {report.sessionId}</p>
          <h2 className="text-xl font-semibold text-charcoal-900">
            {report.candidateName} — {report.position ?? "—"}
          </h2>
          <p className="mt-1 text-xs text-charcoal-500">
            {formatDate(new Date(report.startedAt))} · Observed by {report.observerName}
          </p>
        </div>
        <div className="flex gap-2">
          <Button size="sm" className="gap-1.5" onClick={() => window.open(reportPdfUrl(report.sessionId), "_blank")}>
            <Download className="size-3.5" /> Export PDF
          </Button>
          <Button size="sm" variant="secondary" disabled className="gap-1.5">
            <FileSpreadsheet className="size-3.5" /> CSV
          </Button>
          <Button size="sm" variant="secondary" disabled className="gap-1.5">
            <FileJson className="size-3.5" /> JSON
          </Button>
        </div>
      </motion.div>

      {/* Executive summary */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <FileText className="size-4 text-nile-800" />
            <CardTitle>Executive Summary</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-sm leading-relaxed text-charcoal-700">{report.executiveSummary}</p>
        </CardContent>
      </Card>

      <div className="grid gap-6 lg:grid-cols-2">
        <TrustDNACard trustDNA={trustDNA} compact />

        <Card>
          <CardHeader>
            <div>
              <CardTitle>Decision Confidence</CardTitle>
              <CardDescription>Human Decision Support — not an automated decision.</CardDescription>
            </div>
            <Badge tone={meta.tone}>{meta.label}</Badge>
          </CardHeader>
          <CardContent>
            <p className="tabular text-4xl font-semibold text-charcoal-900">{recommendation.confidence}%</p>
            <ul className="mt-4 space-y-1.5">
              {recommendation.reasons.map((r) => (
                <li key={r} className="flex items-start gap-2 text-sm text-charcoal-600">
                  <span className="mt-1.5 size-1 shrink-0 rounded-full bg-nile-700" />
                  {r}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      </div>

      {/* Evidence table */}
      <Card>
        <CardHeader>
          <CardTitle>Evidence Summary</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-charcoal-100 text-left text-xs text-charcoal-500">
                <th className="px-5 py-3 font-medium">Time</th>
                <th className="px-5 py-3 font-medium">Evidence</th>
                <th className="px-5 py-3 font-medium">Severity</th>
                <th className="px-5 py-3 font-medium">Confidence</th>
              </tr>
            </thead>
            <tbody>
              {evidence.length === 0 && (
                <tr>
                  <td colSpan={4} className="px-5 py-6 text-center text-charcoal-500">
                    No significant evidence was recorded.
                  </td>
                </tr>
              )}
              {evidence.map((e) => {
                const sev = SEVERITY_META[e.severity];
                return (
                  <tr key={e.id} className="border-b border-charcoal-100 last:border-0">
                    <td className="px-5 py-3.5 text-charcoal-500">
                      {new Date(e.timestamp).toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" })}
                    </td>
                    <td className="px-5 py-3.5 font-medium text-charcoal-800">{e.title}</td>
                    <td className="px-5 py-3.5">
                      <Badge tone={sev.tone === "neutral" ? "neutral" : sev.tone}>{sev.label}</Badge>
                    </td>
                    <td className="tabular px-5 py-3.5 text-charcoal-800">{e.confidence}%</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </CardContent>
      </Card>

      {/* Privacy summary */}
      <Card className="bg-papyrus/40 border-papyrus-deep">
        <CardContent className="flex items-center gap-3 p-5">
          <ShieldCheck className="size-5 shrink-0 text-turquoise-700" />
          <p className="text-xs leading-relaxed text-nile-900">{report.privacyStatement.join(" ")}</p>
        </CardContent>
      </Card>
    </div>
  );
}
