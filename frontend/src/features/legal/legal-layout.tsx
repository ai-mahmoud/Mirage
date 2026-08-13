import * as React from "react";
import { Link } from "react-router-dom";
import { LogoMark, Wordmark } from "@/components/shared/logo-mark";

export function LegalLayout({
  title,
  version,
  children,
}: {
  title: string;
  version: string;
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-maat-white">
      <header className="border-b border-charcoal-200 bg-white">
        <div className="mx-auto flex max-w-3xl items-center gap-2.5 px-6 py-4">
          <Link to="/" className="flex items-center gap-2.5">
            <LogoMark />
            <Wordmark className="text-base" />
          </Link>
        </div>
      </header>
      <main className="mx-auto max-w-3xl px-6 py-12">
        <h1 className="text-2xl font-semibold tracking-tight text-charcoal-900">{title}</h1>
        <p className="mt-1 text-xs text-charcoal-500">Effective {version}</p>
        <div className="mt-8 space-y-6 text-sm leading-relaxed text-charcoal-700">{children}</div>
      </main>
    </div>
  );
}

export function LegalSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section>
      <h2 className="text-base font-semibold text-charcoal-900">{title}</h2>
      <div className="mt-2 space-y-3">{children}</div>
    </section>
  );
}
