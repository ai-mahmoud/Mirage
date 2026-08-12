// The only module that talks to the backend. Every other file imports
// named functions from here — never calls fetch() directly — so the
// wire contract has exactly one place to change if it drifts.
import type {
  CreateSessionPayload,
  LoginPayload,
  RawEventOut,
  SessionReportRaw,
  SessionResponseRaw,
  SignupPayload,
  TokenResponseRaw,
  TrustStatusResponseRaw,
  UserResponseRaw,
} from "@/types/api";

const API_BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "http://localhost:8001";

// The bearer token issued by POST /auth/signup or /auth/login. Kept here
// (not re-read from storage per request) so auth-context.tsx's login/
// signup/logout are the only places that decide when it changes;
// localStorage is just where it survives a page reload.
const TOKEN_STORAGE_KEY = "maat_access_token";
let authToken: string | null = null;
try {
  authToken = localStorage.getItem(TOKEN_STORAGE_KEY);
} catch {
  /* storage unavailable (e.g. private browsing) — stay logged out */
}

export function setAuthToken(token: string | null): void {
  authToken = token;
  try {
    if (token) localStorage.setItem(TOKEN_STORAGE_KEY, token);
    else localStorage.removeItem(TOKEN_STORAGE_KEY);
  } catch {
    /* noop */
  }
}

export function getAuthToken(): string | null {
  return authToken;
}

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function authHeaders(): Record<string, string> {
  return authToken ? { Authorization: `Bearer ${authToken}` } : {};
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...authHeaders(), ...init?.headers },
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new ApiError(body || `Request to ${path} failed with ${res.status}`, res.status);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

// --- auth ---

export function signup(payload: SignupPayload): Promise<TokenResponseRaw> {
  return apiFetch("/auth/signup", { method: "POST", body: JSON.stringify(payload) });
}

export function login(payload: LoginPayload): Promise<TokenResponseRaw> {
  return apiFetch("/auth/login", { method: "POST", body: JSON.stringify(payload) });
}

export function getMe(): Promise<UserResponseRaw> {
  return apiFetch("/auth/me");
}

// --- sessions ---

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

// PDF export requires the same bearer auth as every other route, so a
// plain <a href>/window.open (no way to attach a header) would 401 —
// fetch it as a blob with the real auth header instead, and hand the
// caller a local object URL to open/download.
export async function downloadReportPdf(sessionId: string): Promise<string> {
  const res = await fetch(`${API_BASE}/sessions/${sessionId}/report/pdf`, { headers: authHeaders() });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new ApiError(body || `PDF export failed with ${res.status}`, res.status);
  }
  const blob = await res.blob();
  return URL.createObjectURL(blob);
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
