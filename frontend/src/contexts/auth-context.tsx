import * as React from "react";

interface AuthUser {
  name: string;
  email: string;
  initials: string;
  organization: string;
}

interface AuthContextValue {
  user: AuthUser | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<boolean>;
  logout: () => void;
}

const DEMO_USER: AuthUser = {
  name: "Demo Observer",
  email: "demo@platform.ai",
  initials: "DO",
  organization: "MAAT Hackathon Workspace",
};

const AuthContext = React.createContext<AuthContextValue | undefined>(undefined);

const STORAGE_KEY = "maat_demo_session";

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = React.useState<AuthUser | null>(() => {
    try {
      return sessionStorage.getItem(STORAGE_KEY) ? DEMO_USER : null;
    } catch {
      return null;
    }
  });

  const login = React.useCallback(async (_email: string, _password: string) => {
    await new Promise((r) => setTimeout(r, 500));
    setUser(DEMO_USER);
    try {
      sessionStorage.setItem(STORAGE_KEY, "1");
    } catch {
      /* noop */
    }
    return true;
  }, []);

  const logout = React.useCallback(() => {
    setUser(null);
    try {
      sessionStorage.removeItem(STORAGE_KEY);
    } catch {
      /* noop */
    }
  }, []);

  const value = React.useMemo(
    () => ({ user, isAuthenticated: !!user, login, logout }),
    [user, login, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = React.useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
