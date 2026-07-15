import { cn } from "@/lib/utils";

export function LogoMark({ className, size = 28 }: { className?: string; size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      className={cn("shrink-0", className)}
      aria-hidden="true"
    >
      <rect width="32" height="32" rx="9" className="fill-nile-900" />
      <path
        d="M16 7 L16 25 M9 12 L23 12"
        stroke="#D4AF37"
        strokeWidth="1.6"
        strokeLinecap="round"
      />
      <circle cx="9" cy="12" r="2.4" className="fill-maat-white" />
      <circle cx="23" cy="12" r="2.4" className="fill-maat-white" />
      <path d="M16 12 L16 25" stroke="#FAFAF8" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  );
}

export function Wordmark({ className }: { className?: string }) {
  return (
    <span className={cn("font-semibold tracking-tight text-charcoal-900", className)}>
      MAAT
    </span>
  );
}
