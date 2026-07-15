import { Outlet } from "react-router-dom";
import { LogoMark, Wordmark } from "@/components/shared/logo-mark";
import { Scale, Feather, Eye } from "lucide-react";

const PRINCIPLES = [
  { icon: Feather, label: "Evidence before conclusions" },
  { icon: Scale, label: "Balanced, multi-signal reasoning" },
  { icon: Eye, label: "Human oversight, always" },
];

export function AuthLayout() {
  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <div className="relative hidden flex-col justify-between overflow-hidden bg-nile-900 p-12 text-white lg:flex">
        <div className="bg-grid-faint absolute inset-0 opacity-30" />
        <div className="balance-glow absolute -top-24 right-0 h-96 w-96 rounded-full" />
        <div className="relative flex items-center gap-2.5">
          <LogoMark />
          <Wordmark className="text-white text-lg" />
        </div>
        <div className="relative max-w-md">
          <h2 className="text-3xl font-semibold leading-tight tracking-tight">
            Evidence-based human trust for digital decisions.
          </h2>
          <p className="mt-4 text-sm text-nile-100/80">
            Transform behavioral signals into transparent decision confidence through explainable AI —
            without invasive surveillance.
          </p>
          <ul className="mt-8 space-y-3">
            {PRINCIPLES.map(({ icon: Icon, label }) => (
              <li key={label} className="flex items-center gap-3 text-sm text-nile-50">
                <span className="flex size-8 items-center justify-center rounded-full bg-white/10">
                  <Icon className="size-4 text-gold-500" />
                </span>
                {label}
              </li>
            ))}
          </ul>
        </div>
        <p className="relative text-xs text-nile-100/50">© {new Date().getFullYear()} MAAT — Human Decision Confidence Platform</p>
      </div>

      <div className="flex flex-col items-center justify-center bg-maat-white px-6 py-12">
        <div className="w-full max-w-sm">
          <Outlet />
        </div>
      </div>
    </div>
  );
}
