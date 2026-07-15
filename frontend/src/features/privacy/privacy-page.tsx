import { EyeOff, Lock, Cpu, UserCheck, ShieldCheck } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { SIGNAL_TAXONOMY } from "@/data/demo-data";
import { Badge } from "@/components/ui/badge";

const PRINCIPLES = [
  { icon: EyeOff, title: "No Keystroke Content Stored", body: "Only timing metadata is analyzed. What is typed is never recorded or inspected." },
  { icon: Lock, title: "No Video or Audio Stored", body: "No microphone recording. No persistent video storage of any kind." },
  { icon: Cpu, title: "Local Processing Enabled", body: "Behavioral features are computed close to the source wherever feasible." },
  { icon: UserCheck, title: "Human Review Required", body: "The AI never makes an autonomous hiring decision. A person always reviews the evidence." },
];

export function PrivacyPage() {
  return (
    <div className="space-y-6">
      <Card className="bg-nile-900 text-white border-0">
        <CardContent className="flex items-center gap-4 p-6">
          <ShieldCheck className="size-8 shrink-0 text-gold-500" />
          <div>
            <h2 className="text-lg font-semibold">Privacy by Design</h2>
            <p className="mt-1 text-sm text-nile-100/80">
              Reinforced continuously across every screen — not a policy buried in a footer.
            </p>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 sm:grid-cols-2">
        {PRINCIPLES.map(({ icon: Icon, title, body }) => (
          <Card key={title}>
            <CardContent className="p-5">
              <div className="flex size-9 items-center justify-center rounded-full bg-turquoise-100 text-turquoise-700">
                <Icon className="size-4.5" />
              </div>
              <h3 className="mt-3 text-sm font-semibold text-charcoal-800">{title}</h3>
              <p className="mt-1.5 text-xs leading-relaxed text-charcoal-500">{body}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <div>
            <CardTitle>Signal Privacy Classification</CardTitle>
            <CardDescription>Every collected signal is documented with a privacy impact level.</CardDescription>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-charcoal-100 text-left text-xs text-charcoal-500">
                <th className="px-5 py-3 font-medium">Signal</th>
                <th className="px-5 py-3 font-medium">Category</th>
                <th className="px-5 py-3 font-medium">Reliability</th>
                <th className="px-5 py-3 font-medium">Privacy Impact</th>
              </tr>
            </thead>
            <tbody>
              {SIGNAL_TAXONOMY.map((s) => (
                <tr key={s.id} className="border-b border-charcoal-100 last:border-0">
                  <td className="px-5 py-3 font-medium text-charcoal-800">{s.name}</td>
                  <td className="px-5 py-3 text-charcoal-600">{s.category}</td>
                  <td className="px-5 py-3 text-charcoal-600">{s.reliability}</td>
                  <td className="px-5 py-3">
                    <Badge tone={s.privacy === "Low" ? "success" : s.privacy === "Medium" ? "warning" : "danger"}>
                      {s.privacy}
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}
