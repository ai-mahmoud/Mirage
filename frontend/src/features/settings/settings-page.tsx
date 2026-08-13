import * as React from "react";
import { Link, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input, Label, FieldError } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useAuth } from "@/contexts/auth-context";
import { ApiError, deleteMyOrganization, exportMyData, getMyOrganization, startBillingPortal } from "@/lib/api-client";

export function SettingsPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [portalError, setPortalError] = React.useState<string | null>(null);
  const [openingPortal, setOpeningPortal] = React.useState(false);
  const [exporting, setExporting] = React.useState(false);
  const [exportError, setExportError] = React.useState<string | null>(null);
  const [confirmingDelete, setConfirmingDelete] = React.useState(false);
  const [deleting, setDeleting] = React.useState(false);
  const [deleteError, setDeleteError] = React.useState<string | null>(null);

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

  async function handleExport() {
    setExportError(null);
    setExporting(true);
    try {
      const data = await exportMyData();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `mirage-data-export-${new Date().toISOString().slice(0, 10)}.json`;
      link.click();
      URL.revokeObjectURL(url);
    } catch {
      setExportError("Couldn't export your data — please try again.");
    } finally {
      setExporting(false);
    }
  }

  async function handleDeleteOrganization() {
    setDeleteError(null);
    setDeleting(true);
    try {
      await deleteMyOrganization();
      logout();
      navigate("/");
    } catch (err) {
      setDeleteError(
        err instanceof ApiError && err.status === 403
          ? "Only the organization owner can delete it."
          : "Couldn't delete the organization — please try again."
      );
      setDeleting(false);
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
          <div>
            <CardTitle>Data &amp; Privacy</CardTitle>
            <CardDescription>
              Read our{" "}
              <Link to="/legal/privacy-policy" target="_blank" className="text-nile-700 hover:underline">
                Privacy Policy
              </Link>{" "}
              and{" "}
              <Link to="/legal/terms-of-service" target="_blank" className="text-nile-700 hover:underline">
                Terms of Service
              </Link>
              . Export or delete everything this platform holds about your organization at any time.
            </CardDescription>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <FieldError>{exportError ?? undefined}</FieldError>
          <Button variant="secondary" className="gap-2" onClick={handleExport} disabled={exporting}>
            {exporting && <Loader2 className="size-4 animate-spin" />}
            Export My Data
          </Button>

          <div className="border-t border-charcoal-200 pt-4">
            <FieldError>{deleteError ?? undefined}</FieldError>
            {!confirmingDelete ? (
              <Button variant="danger" onClick={() => setConfirmingDelete(true)}>
                Delete Organization
              </Button>
            ) : (
              <div className="space-y-2.5 rounded-[var(--radius-input)] border border-crimson-200 bg-crimson-50 p-3.5">
                <p className="text-xs text-crimson-700">
                  This permanently deletes every session, evidence card, and user in your organization.
                  This cannot be undone.
                </p>
                <div className="flex gap-2.5">
                  <Button
                    variant="danger"
                    size="sm"
                    className="gap-2"
                    onClick={handleDeleteOrganization}
                    disabled={deleting}
                  >
                    {deleting && <Loader2 className="size-4 animate-spin" />}
                    Yes, permanently delete
                  </Button>
                  <Button variant="secondary" size="sm" onClick={() => setConfirmingDelete(false)} disabled={deleting}>
                    Cancel
                  </Button>
                </div>
              </div>
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
