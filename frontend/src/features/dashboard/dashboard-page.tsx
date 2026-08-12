import { motion } from "framer-motion";
import { Link, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Activity, Cpu, Gauge, PlusCircle, FileClock, PlayCircle, ArrowUpRight } from "lucide-react";
import { Bar, BarChart, ResponsiveContainer, XAxis, Tooltip, CartesianGrid, PieChart, Pie, Cell, Legend } from "recharts";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { SkeletonCard, Skeleton } from "@/components/ui/skeleton";
import { checkHealth, listSessions } from "@/lib/api-client";
import { deriveActivityFeed, mapSessionSummary } from "@/lib/session-mappers";
import { bandFromScore, BAND_META, RECOMMENDATION_META } from "@/lib/confidence";
import { useCurrentSession } from "@/contexts/session-context";
import type { SessionSummary } from "@/types/domain";

const PIE_COLORS = ["#2e8b57", "#2a9d8f", "#e9a03b", "#a63d40", "#7a7a7a"];
const BAND_ORDER = ["very-high", "high", "moderate", "low", "very-low"] as const;

function isToday(iso: string): boolean {
  const d = new Date(iso);
  const now = new Date();
  return d.toDateString() === now.toDateString();
}

function dailySessionCounts(sessions: SessionSummary[]) {
  const days: { key: string; day: string; sessions: number }[] = [];
  for (let i = 6; i >= 0; i--) {
    const d = new Date();
    d.setDate(d.getDate() - i);
    days.push({ key: d.toDateString(), day: d.toLocaleDateString(undefined, { weekday: "short" }), sessions: 0 });
  }
  for (const s of sessions) {
    const key = new Date(s.startedAt).toDateString();
    const bucket = days.find((d) => d.key === key);
    if (bucket) bucket.sessions += 1;
  }
  return days;
}

function trustDistribution(sessions: SessionSummary[]) {
  const counts: Record<string, number> = { "very-high": 0, high: 0, moderate: 0, low: 0, "very-low": 0 };
  for (const s of sessions) {
    const band = bandFromScore(s.trustDNA.sessionAuthenticity);
    counts[band] += 1;
  }
  return BAND_ORDER.map((band) => ({ band: BAND_META[band].label, count: counts[band] }));
}

export function DashboardPage() {
  const navigate = useNavigate();
  const { setCurrentSessionId } = useCurrentSession();

  const { data: rawSessions, isLoading } = useQuery({ queryKey: ["sessions"], queryFn: listSessions, refetchInterval: 5000 });
  const { data: healthy } = useQuery({ queryKey: ["health"], queryFn: checkHealth, refetchInterval: 10_000 });

  if (isLoading) {
    return (
      <div className="space-y-8">
        <div className="flex items-center justify-between">
          <div className="space-y-2">
            <Skeleton className="h-6 w-64" />
            <Skeleton className="h-3.5 w-80" />
          </div>
          <div className="flex gap-3">
            <Skeleton className="h-9 w-32 rounded-[var(--radius-button)]" />
            <Skeleton className="h-9 w-40 rounded-[var(--radius-button)]" />
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
        <div className="grid gap-6 lg:grid-cols-3">
          <Card className="lg:col-span-2">
            <CardContent className="p-5">
              <Skeleton className="h-52 w-full" />
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-5">
              <Skeleton className="h-52 w-full rounded-full" />
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  const sessions: SessionSummary[] = (rawSessions ?? []).map(mapSessionSummary);
  const todaysSessions = sessions.filter((s) => isToday(s.startedAt)).length;
  const averageConfidence = sessions.length
    ? Math.round(sessions.reduce((sum, s) => sum + s.decisionConfidence, 0) / sessions.length)
    : 0;

  const kpis = [
    { icon: Gauge, label: "System Health", value: healthy === undefined ? "Checking…" : healthy ? "Operational" : "Unreachable", chip: "bg-emerald-100 text-emerald-700" },
    { icon: Cpu, label: "Behavior Engine", value: healthy === undefined ? "Checking…" : healthy ? "Running" : "Unreachable", chip: "bg-turquoise-100 text-turquoise-700" },
    { icon: PlayCircle, label: "Today's Sessions", value: String(todaysSessions), chip: "bg-nile-100 text-nile-700" },
    { icon: Activity, label: "Avg. Decision Confidence", value: sessions.length ? `${averageConfidence}%` : "—", chip: "bg-gold-100 text-gold-700" },
  ];

  const activity = deriveActivityFeed(sessions);
  const daily = dailySessionCounts(sessions);
  const distribution = trustDistribution(sessions);

  const openLastReport = () => {
    if (sessions[0]) setCurrentSessionId(sessions[0].id);
    navigate("/reports");
  };

  const viewSession = (id: string) => {
    setCurrentSessionId(id);
    navigate("/reports");
  };

  return (
    <div className="space-y-8">
      {/* Quick actions */}
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <h2 className="text-[22px] font-semibold tracking-tight text-charcoal-900">Good to see you, Demo Observer.</h2>
          <p className="mt-1 text-sm text-charcoal-500">Here is what's happening across your workspace today.</p>
        </div>
        <div className="flex gap-3">
          <Button variant="secondary" size="sm" className="gap-1.5" onClick={openLastReport} disabled={!sessions.length}>
            <FileClock className="size-4" /> Open Last Report
          </Button>
          <Link to="/live-session">
            <Button size="sm" className="gap-1.5">
              <PlusCircle className="size-4" /> Create New Session
            </Button>
          </Link>
        </div>
      </div>

      {/* KPI cards */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {kpis.map(({ icon: Icon, label, value, chip }, i) => (
          <motion.div key={label} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05, duration: 0.4, ease: [0.16, 1, 0.3, 1] }}>
            <Card interactive className="h-full">
              <CardContent className="p-5">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium text-charcoal-500">{label}</span>
                  <span className={`flex size-8 items-center justify-center rounded-full ${chip}`}>
                    <Icon className="size-4" />
                  </span>
                </div>
                <p className="tabular mt-3.5 text-[26px] font-semibold leading-none tracking-tight text-charcoal-900">{value}</p>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Charts */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <div>
              <CardTitle>Daily Sessions</CardTitle>
              <CardDescription>Sessions observed per day this week</CardDescription>
            </div>
          </CardHeader>
          <CardContent className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={daily}>
                <CartesianGrid vertical={false} stroke="#eceae4" />
                <XAxis dataKey="day" tickLine={false} axisLine={false} tick={{ fontSize: 12, fill: "#7a7a7a" }} />
                <Tooltip cursor={{ fill: "#f2f6fb" }} contentStyle={{ borderRadius: 12, border: "1px solid #d8d8d5", fontSize: 12 }} />
                <Bar dataKey="sessions" fill="#123c69" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div>
              <CardTitle>Trust Distribution</CardTitle>
              <CardDescription>All recorded sessions</CardDescription>
            </div>
          </CardHeader>
          <CardContent className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={distribution} dataKey="count" nameKey="band" innerRadius={45} outerRadius={70} paddingAngle={2}>
                  {distribution.map((_, i) => (
                    <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Legend verticalAlign="bottom" height={36} iconSize={8} wrapperStyle={{ fontSize: 11 }} />
                <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid #d8d8d5", fontSize: 12 }} />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Live status */}
        <Card>
          <CardHeader>
            <CardTitle>Live Status</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {["AI Engine", "Tracking Engine", "Evidence Engine", "Recommendation Engine"].map((s) => (
              <div key={s} className="flex items-center justify-between rounded-lg px-2.5 py-2 text-sm transition-colors hover:bg-charcoal-50">
                <span className="text-charcoal-700">{s}</span>
                <Badge tone={healthy ? "success" : "danger"} dot>
                  {healthy ? "Running" : "Unreachable"}
                </Badge>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Activity feed */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Activity Feed</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {activity.length === 0 && <p className="text-sm text-charcoal-500">No activity yet — start a session to see it here.</p>}
            {activity.map((a) => (
              <div key={a.id} className="flex items-start justify-between gap-4 border-b border-charcoal-100 pb-3 last:border-0 last:pb-0">
                <div>
                  <p className="text-sm font-medium text-charcoal-800">{a.label}</p>
                  <p className="text-xs text-charcoal-500">{a.detail}</p>
                </div>
                <span className="whitespace-nowrap text-[11px] text-charcoal-400">
                  {new Date(a.timestamp).toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" })}
                </span>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      {/* Recent sessions */}
      <Card>
        <CardHeader>
          <div>
            <CardTitle>Recent Sessions</CardTitle>
            <CardDescription>Showing the {Math.min(sessions.length, 8)} most recent of {sessions.length}</CardDescription>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-charcoal-100 text-left text-[11px] uppercase tracking-wide text-charcoal-400">
                <th className="px-5 py-3.5 font-medium">Candidate</th>
                <th className="px-5 py-3.5 font-medium">Position</th>
                <th className="px-5 py-3.5 font-medium">Confidence</th>
                <th className="px-5 py-3.5 font-medium">Recommendation</th>
                <th className="px-5 py-3.5 font-medium">Status</th>
                <th className="px-5 py-3.5" />
              </tr>
            </thead>
            <tbody>
              {sessions.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-5 py-6 text-center text-sm text-charcoal-500">
                    No sessions yet — create one to get started.
                  </td>
                </tr>
              )}
              {sessions.slice(0, 8).map((s) => {
                const meta = RECOMMENDATION_META[s.recommendation];
                return (
                  <tr key={s.id} className="border-b border-charcoal-100 text-[13px] transition-colors last:border-0 hover:bg-nile-50/50">
                    <td className="px-5 py-3.5 font-medium text-charcoal-800">{s.candidateName}</td>
                    <td className="px-5 py-3.5 text-charcoal-600">{s.position}</td>
                    <td className="tabular px-5 py-3.5 font-medium text-charcoal-800">{s.decisionConfidence}%</td>
                    <td className="px-5 py-3.5">
                      <Badge tone={meta.tone}>{meta.label}</Badge>
                    </td>
                    <td className="px-5 py-3.5 capitalize text-charcoal-600">{s.status}</td>
                    <td className="px-5 py-3.5 text-right">
                      <button
                        onClick={() => viewSession(s.id)}
                        className="inline-flex items-center gap-1 text-xs font-medium text-nile-800 transition-colors hover:text-nile-600 hover:underline"
                      >
                        View <ArrowUpRight className="size-3" />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}
