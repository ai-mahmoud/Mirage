import * as React from "react";
import { ApiError, getMe, login as apiLogin, setAuthToken, signup as apiSignup } from "@/lib/api-client";
import type { UserResponseRaw } from "@/types/api";

interface AuthUser {
  name: string;
  email: string;
  initials: string;
  organization: string;
  role: string;
}

interface AuthContextValue {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (orgName: string, email: string, password: string) => Promise<void>;
  logout: () => void;
}

function toAuthUser(raw: UserResponseRaw, orgName?: string): AuthUser {
  const namePart = raw.email.split("@")[0] ?? raw.email;
  return {
    name: namePart,
    email: raw.email,
    initials: namePart.slice(0, 2).toUpperCase(),
    organization: orgName ?? raw.orgId,
    role: raw.role,
  };
}

const AuthContext = React.createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = React.useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = React.useState(true);

  // On mount, a token surviving from a previous session (see
  // api-client.ts's localStorage persistence) is validated against
  // GET /auth/me rather than trusted blindly — an expired/revoked token
  // should bounce back to the login screen, not render a stale session.
  React.useEffect(() => {
    let cancelled = false;
    getMe()
      .then((raw) => {
        if (!cancelled) setUser(toAuthUser(raw));
      })
      .catch(() => {
        if (!cancelled) setAuthToken(null);
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const login = React.useCallback(async (email: string, password: string) => {
    const resp = await apiLogin({ email, password });
    setAuthToken(resp.accessToken);
    setUser(toAuthUser(resp.user));
  }, []);

  const signup = React.useCallback(async (orgName: string, email: string, password: string) => {
    const resp = await apiSignup({ orgName, email, password });
    setAuthToken(resp.accessToken);
    setUser(toAuthUser(resp.user, orgName));
  }, []);

  const logout = React.useCallback(() => {
    setAuthToken(null);
    setUser(null);
  }, []);

  const value = React.useMemo(
    () => ({ user, isAuthenticated: !!user, isLoading, login, signup, logout }),
    [user, isLoading, login, signup, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = React.useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

export { ApiError };
