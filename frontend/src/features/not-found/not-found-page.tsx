import { Link } from "react-router-dom";
import { Compass } from "lucide-react";
import { Button } from "@/components/ui/button";

export function NotFoundPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-maat-white px-6 text-center">
      <div className="flex size-14 items-center justify-center rounded-full bg-nile-50 text-nile-800">
        <Compass className="size-6" />
      </div>
      <h1 className="mt-6 text-2xl font-semibold text-charcoal-900">Page not found</h1>
      <p className="mt-2 max-w-sm text-sm text-charcoal-500">
        The screen you're looking for doesn't exist in this workspace. Every screen in MAAT exists to answer one
        question — this one doesn't have an answer yet.
      </p>
      <Link to="/dashboard" className="mt-6">
        <Button>Return to Dashboard</Button>
      </Link>
    </div>
  );
}
