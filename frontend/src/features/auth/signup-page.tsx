import * as React from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Loader2, UserPlus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input, Label, FieldError } from "@/components/ui/input";
import { useAuth } from "@/contexts/auth-context";
import { ApiError } from "@/lib/api-client";

export function SignupPage() {
  const [orgName, setOrgName] = React.useState("");
  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const { signup } = useAuth();
  const navigate = useNavigate();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await signup(orgName, email, password);
      navigate("/dashboard");
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setError("That email is already registered — sign in instead.");
      } else {
        setError("Could not create your workspace — please try again.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35 }}>
      <h1 className="text-2xl font-semibold text-charcoal-900">Create your workspace</h1>
      <p className="mt-1.5 text-sm text-charcoal-500">Start running behavioral-intelligence sessions in minutes.</p>

      <form className="mt-8 space-y-4" onSubmit={handleSubmit}>
        <div>
          <Label htmlFor="orgName">Organization name</Label>
          <Input id="orgName" required value={orgName} onChange={(e) => setOrgName(e.target.value)} autoComplete="organization" />
        </div>
        <div>
          <Label htmlFor="email">Email</Label>
          <Input
            id="email"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="username"
          />
        </div>
        <div>
          <Label htmlFor="password">Password</Label>
          <Input
            id="password"
            type="password"
            required
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="new-password"
          />
        </div>
        <FieldError>{error ?? undefined}</FieldError>

        <Button type="submit" className="w-full gap-2" disabled={loading}>
          {loading ? <Loader2 className="size-4 animate-spin" /> : <UserPlus className="size-4" />}
          {loading ? "Creating workspace..." : "Create Workspace"}
        </Button>
      </form>

      <p className="mt-6 text-center text-sm text-charcoal-500">
        Already have a workspace?{" "}
        <Link to="/login" className="font-medium text-nile-700 hover:underline">
          Sign in
        </Link>
      </p>
    </motion.div>
  );
}
