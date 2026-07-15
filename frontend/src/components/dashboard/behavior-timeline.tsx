import { motion } from "framer-motion";
import type { TimelineEvent } from "@/types/domain";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { cn } from "@/lib/utils";

const DOT_TONE: Record<TimelineEvent["severity"] extends undefined ? never : string, string> = {
  low: "bg-turquoise-500",
  medium: "bg-amber-500",
  high: "bg-crimson-500",
};

export function BehaviorTimeline({ events }: { events: TimelineEvent[] }) {
  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle>Behavioral Timeline</CardTitle>
          <CardDescription>Entire session history, in order of occurrence.</CardDescription>
        </div>
      </CardHeader>
      <CardContent>
        <ol className="relative ml-3 space-y-5 border-l border-charcoal-200 pl-6">
          {events.map((event, i) => (
            <motion.li
              key={event.id}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.05 }}
              className="relative"
            >
              <span
                className={cn(
                  "absolute -left-[31px] top-1 size-3 rounded-full ring-4 ring-white",
                  event.severity ? DOT_TONE[event.severity] : "bg-nile-700"
                )}
              />
              <p className="text-sm font-medium text-charcoal-800">{event.label}</p>
              {event.detail && <p className="text-xs text-charcoal-500">{event.detail}</p>}
              <p className="mt-0.5 text-[11px] text-charcoal-400">
                {new Date(event.timestamp).toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
              </p>
            </motion.li>
          ))}
        </ol>
      </CardContent>
    </Card>
  );
}
