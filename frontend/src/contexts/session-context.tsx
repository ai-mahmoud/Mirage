import * as React from "react";

interface CurrentSessionContextValue {
  currentSessionId: string | null;
  setCurrentSessionId: (id: string | null) => void;
}

const CurrentSessionContext = React.createContext<CurrentSessionContextValue | undefined>(undefined);

const STORAGE_KEY = "maat_current_session_id";

// Mirrors auth-context.tsx's sessionStorage pattern: lets Report / Trust
// DNA / Evidence / Timeline / Recommendations pages all find "which
// session to show" after navigating away from Live Session, without
// route params or prop drilling.
export function CurrentSessionProvider({ children }: { children: React.ReactNode }) {
  const [currentSessionId, setCurrentSessionIdState] = React.useState<string | null>(() => {
    try {
      return sessionStorage.getItem(STORAGE_KEY);
    } catch {
      return null;
    }
  });

  const setCurrentSessionId = React.useCallback((id: string | null) => {
    setCurrentSessionIdState(id);
    try {
      if (id) sessionStorage.setItem(STORAGE_KEY, id);
      else sessionStorage.removeItem(STORAGE_KEY);
    } catch {
      /* noop */
    }
  }, []);

  const value = React.useMemo(
    () => ({ currentSessionId, setCurrentSessionId }),
    [currentSessionId, setCurrentSessionId]
  );

  return <CurrentSessionContext.Provider value={value}>{children}</CurrentSessionContext.Provider>;
}

export function useCurrentSession() {
  const ctx = React.useContext(CurrentSessionContext);
  if (!ctx) throw new Error("useCurrentSession must be used within CurrentSessionProvider");
  return ctx;
}
