import { Link } from "react-router-dom";
import { FileText } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

export function NoActiveSession({ message = "No session selected yet." }: { message?: string }) {
  return (
    <Card className="mx-auto max-w-xl">
      <CardContent className="space-y-3 p-8 text-center">
        <FileText className="mx-auto size-8 text-charcoal-300" />
        <p className="text-sm text-charcoal-600">{message}</p>
        <Link to="/live-session" className="text-sm font-medium text-nile-800 hover:underline">
          Start a session
        </Link>
      </CardContent>
    </Card>
  );
}
