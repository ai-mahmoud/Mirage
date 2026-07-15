import * as React from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Loader2, LogIn } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input, Label } from "@/components/ui/input";
import { useAuth } from "@/contexts/auth-context";

export function LoginPage() {
  const [email, setEmail] = React.useState("demo@platform.ai");
  const [password, setPassword] = React.useState("••••••••");
  const [loading, setLoading] = React.useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    await login(email, password);
    setLoading(false);
    navigate("/dashboard");
  }

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35 }}>
      <h1 className="text-2xl font-semibold text-charcoal-900">Welcome back</h1>
      <p className="mt-1.5 text-sm text-charcoal-500">Sign in to continue to your workspace.</p>

      <form className="mt-8 space-y-4" onSubmit={handleSubmit}>
        <div>
          <Label htmlFor="email">Email</Label>
          <Input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="username" />
        </div>
        <div>
          <Label htmlFor="password">Password</Label>
          <Input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" />
        </div>

        <Button type="submit" className="w-full gap-2" disabled={loading}>
          {loading ? <Loader2 className="size-4 animate-spin" /> : <LogIn className="size-4" />}
          {loading ? "Signing in..." : "Sign In"}
        </Button>
      </form>

      <div className="mt-6 rounded-[var(--radius-card)] border border-charcoal-200 bg-charcoal-100/50 p-4 text-xs text-charcoal-500">
        <p className="font-medium text-charcoal-700">Hackathon demo credentials are pre-filled.</p>
        <p className="mt-1">One click. Login. Done — no need to waste demo time on authentication.</p>
      </div>
    </motion.div>
  );
}
