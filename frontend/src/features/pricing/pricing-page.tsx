import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import { Check, Loader2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { FieldError } from "@/components/ui/input";
import { ApiError, getMyOrganization, startCheckout } from "@/lib/api-client";

const PLANS = [
  {
    id: "free" as const,
    name: "Free",
    price: "$0",
    cadence: "/month",
    description: "Evaluate the platform with a handful of real sessions.",
    features: ["5 behavioral sessions / month", "Full Trust DNA + evidence engine", "PDF session reports"],
  },
  {
    id: "pro" as const,
    name: "Pro",
    price: "$49",
    cadence: "/month",
    description: "For teams running interviews at volume.",
    features: [
      "Unlimited behavioral sessions",
      "Full Trust DNA + evidence engine",
      "PDF session reports",
      "Priority support",
    ],
  },
];

export function PricingPage() {
  const [checkoutError, setCheckoutError] = React.useState<string | null>(null);
  const [startingCheckout, setStartingCheckout] = React.useState(false);

  const { data: org } = useQuery({
    queryKey: ["organization", "me"],
    queryFn: getMyOrganization,
  });

  async function handleUpgrade() {
    setCheckoutError(null);
    setStartingCheckout(true);
    try {
      const { url } = await startCheckout("pro");
      window.location.href = url;
    } catch (err) {
      setCheckoutError(
        err instanceof ApiError && err.status === 503
          ? "Billing isn't turned on for this deployment yet — contact the team to upgrade."
          : "Couldn't start checkout — please try again."
      );
      setStartingCheckout(false);
    }
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <h2 className="text-xl font-semibold tracking-tight text-charcoal-900">Plans</h2>
        <p className="mt-1 text-sm text-charcoal-500">Choose the plan that fits how many sessions you run.</p>
      </div>

      <FieldError>{checkoutError ?? undefined}</FieldError>

      <div className="grid gap-6 sm:grid-cols-2">
        {PLANS.map((plan) => {
          const isCurrent = org?.planTier === plan.id;
          return (
            <Card key={plan.id} className={plan.id === "pro" ? "border-nile-700" : undefined}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>{plan.name}</CardTitle>
                  {isCurrent && <Badge tone="success">Current plan</Badge>}
                </div>
                <CardDescription>{plan.description}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-5">
                <p className="text-3xl font-semibold text-charcoal-900">
                  {plan.price}
                  <span className="text-sm font-normal text-charcoal-500">{plan.cadence}</span>
                </p>
                <ul className="space-y-2">
                  {plan.features.map((feature) => (
                    <li key={feature} className="flex items-center gap-2 text-sm text-charcoal-700">
                      <Check className="size-4 shrink-0 text-turquoise-600" />
                      {feature}
                    </li>
                  ))}
                </ul>
                {plan.id === "pro" && !isCurrent && (
                  <Button className="w-full gap-2" onClick={handleUpgrade} disabled={startingCheckout}>
                    {startingCheckout && <Loader2 className="size-4 animate-spin" />}
                    {startingCheckout ? "Redirecting to checkout..." : "Upgrade to Pro"}
                  </Button>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
