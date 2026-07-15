import { Lock, EyeOff, Cpu, UserCheck } from "lucide-react";
import type { LiveSignal } from "@/types/domain";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ProgressBar } from "@/components/ui/progress";

const PRIVACY_ITEMS = [
  { icon: EyeOff, label: "No Keystrokes Stored" },
  { icon: Lock, label: "No Video Stored" },
  { icon: Cpu, label: "Local Processing Enabled" },
  { icon: UserCheck, label: "Human Review Required" },
];

export function PrivacyCard() {
  return (
    <Card className="bg-papyrus/40 border-papyrus-deep">
      <CardHeader>
        <CardTitle>Privacy By Design</CardTitle>
      </CardHeader>
      <CardContent>
        <ul className="grid grid-cols-2 gap-3">
          {PRIVACY_ITEMS.map(({ icon: Icon, label }) => (
            <li key={label} className="flex items-center gap-2 text-xs font-medium text-nile-900">
              <Icon className="size-3.5 text-turquoise-600" />
              {label}
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}

export function LiveSignalStream({ signals }: { signals: LiveSignal[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Live Signal Stream</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {signals.map((s) => (
          <div key={s.id}>
            <div className="mb-1.5 flex items-baseline justify-between">
              <span className="text-[13px] text-charcoal-700">{s.label}</span>
              <span className="tabular text-[13px] font-medium text-charcoal-800">
                {s.value}
                {s.unit ? <span className="ml-1 text-[10px] text-charcoal-400">{s.unit}</span> : null}
              </span>
            </div>
            <ProgressBar value={s.value} tone="turquoise" height={5} />
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
