import * as React from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input, Label, FieldError } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useAuth } from "@/contexts/auth-context";
import { ApiError, getMyOrganization, startBillingPortal } from "@/lib/api-client";

export function SettingsPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [portalError, setPortalError] = React.useState<string | null>(null);
  const [openingPortal, setOpeningPortal] = React.useState(false);

  const { data: org } = useQuery({
    queryKey: ["organization", "me"],
    queryFn: getMyOrganization,
  });

  async function handleManageBilling() {
    setPortalError(null);
    setOpeningPortal(true);
    try {
      const { url } = await startBillingPortal();
      window.location.href = url;
    } catch (err) {
      setPortalError(
        err instanceof ApiError && err.status === 404
          ? "No billing account yet — upgrade to a paid plan first."
          : "Couldn't open the billing portal — please try again."
      );
      setOpeningPortal(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <Card>
        <CardHeader>
          <div>
            <CardTitle>Workspace</CardTitle>
            <CardDescription>Your account and organization.</CardDescription>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label>Email</Label>
            <Input value={user?.email ?? ""} readOnly />
          </div>
          <div>
            <Label>Role</Label>
            <Input value={user?.role ?? ""} readOnly />
          </div>
          <div>
            <Label>Organization</Label>
            <Input value={user?.organization ?? ""} readOnly />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Billing</CardTitle>
              <CardDescription>Your current plan and subscription.</CardDescription>
            </div>
            {org && (
              <Badge tone={org.planTier === "pro" ? "gold" : "neutral"}>
                {org.planTier === "pro" ? "Pro" : "Free"}
              </Badge>
            )}
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <FieldError>{portalError ?? undefined}</FieldError>
          <div className="flex gap-3">
            {org?.planTier === "pro" ? (
              <Button variant="secondary" className="gap-2" onClick={handleManageBilling} disabled={openingPortal}>
                {openingPortal && <Loader2 className="size-4 animate-spin" />}
                Manage Billing
              </Button>
            ) : (
              <Button onClick={() => navigate("/pricing")}>Upgrade to Pro</Button>
            )}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Session</CardTitle>
        </CardHeader>
        <CardContent>
          <Button variant="danger" onClick={logout}>
            Sign Out
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
