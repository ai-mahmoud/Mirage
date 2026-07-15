import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center gap-1.5 rounded-[var(--radius-badge)] px-2.5 py-1 text-[11px] font-medium tracking-wide",
  {
    variants: {
      tone: {
        neutral: "bg-charcoal-100 text-charcoal-700",
        nile: "bg-nile-100 text-nile-900",
        gold: "bg-gold-100 text-gold-700",
        turquoise: "bg-turquoise-100 text-turquoise-700",
        success: "bg-emerald-100 text-emerald-700",
        warning: "bg-amber-100 text-amber-700",
        danger: "bg-crimson-100 text-crimson-700",
      },
    },
    defaultVariants: { tone: "neutral" },
  }
);

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement>, VariantProps<typeof badgeVariants> {
  dot?: boolean;
}

export function Badge({ className, tone, dot, children, ...props }: BadgeProps) {
  return (
    <span className={cn(badgeVariants({ tone }), className)} {...props}>
      {dot && <span className="size-1.5 rounded-full bg-current" />}
      {children}
    </span>
  );
}
