import * as React from "react";
import { AnimatePresence, motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { useCurrentSession } from "@/contexts/session-context";
import { CreateSessionForm, type CreateSessionResult } from "./create-session-form";
import { SessionInitializing } from "./session-initializing";
import { LiveDashboard } from "./live-dashboard";

type Stage = "form" | "initializing" | "live";

export function LiveSessionPage() {
  const [stage, setStage] = React.useState<Stage>("form");
  const [session, setSession] = React.useState<CreateSessionResult | null>(null);
  const { setCurrentSessionId } = useCurrentSession();
  const navigate = useNavigate();

  return (
    <AnimatePresence mode="wait">
      {stage === "form" && (
        <motion.div key="form" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
          <CreateSessionForm
            onCreate={(result) => {
              setSession(result);
              setCurrentSessionId(result.sessionId);
              setStage("initializing");
            }}
            onCancel={() => navigate("/dashboard")}
          />
        </motion.div>
      )}

      {stage === "initializing" && (
        <motion.div key="init" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
          <SessionInitializing onComplete={() => setStage("live")} />
        </motion.div>
      )}

      {stage === "live" && session && (
        <motion.div key="live" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
          <LiveDashboard session={session} onEnd={() => navigate("/reports")} />
        </motion.div>
      )}
    </AnimatePresence>
  );
}
