// The only module that talks to the backend. Every other file imports
// named functions from here — never calls fetch() directly — so the
// wire contract has exactly one place to change if it drifts.
import type {
  CreateSessionPayload,
  RawEventOut,
  SessionReportRaw,
  SessionResponseRaw,
  TrustStatusResponseRaw,
} from "@/types/api";

const API_BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "http://localhost:8001";

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new ApiError(body || `Request to ${path} failed with ${res.status}`, res.status);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export function createSession(
  payload: CreateSessionPayload
): Promise<{ sessionId: string; candidateName: string; interviewType: string; status: string }> {
  return apiFetch("/sessions", { method: "POST", body: JSON.stringify(payload) });
}

export function postEvents(sessionId: string, events: RawEventOut[]): Promise<TrustStatusResponseRaw> {
  return apiFetch(`/sessions/${sessionId}/events`, {
    method: "POST",
    body: JSON.stringify({ events }),
  });
}

export function getTrustStatus(sessionId: string): Promise<TrustStatusResponseRaw> {
  return apiFetch(`/sessions/${sessionId}/trust`);
}

export function endSession(sessionId: string): Promise<SessionResponseRaw> {
  return apiFetch(`/sessions/${sessionId}/end`, { method: "POST" });
}

export function getReport(sessionId: string): Promise<SessionReportRaw> {
  return apiFetch(`/sessions/${sessionId}/report`);
}

export function reportPdfUrl(sessionId: string): string {
  return `${API_BASE}/sessions/${sessionId}/report/pdf`;
}

export function listSessions(): Promise<SessionResponseRaw[]> {
  return apiFetch("/sessions");
}

export async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/health`);
    return res.ok;
  } catch {
    return false;
  }
}
