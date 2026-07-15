import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { Feather, Scale, Eye, ShieldCheck, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { LogoMark, Wordmark } from "@/components/shared/logo-mark";

const CAPABILITIES = [
  {
    icon: Feather,
    title: "Capture",
    body: "Collect real-time behavioral signals — mouse dynamics, typing rhythm, focus, and timing — without recording content.",
  },
  {
    icon: Scale,
    title: "Reason",
    body: "Multiple independent signals are weighed together into a six-dimension Trust DNA profile, never a single score.",
  },
  {
    icon: Eye,
    title: "Explain",
    body: "Every recommendation is accompanied by the evidence that produced it, presented before any conclusion.",
  },
  {
    icon: ShieldCheck,
    title: "Support",
    body: "The platform recommends. The human decides. AI never issues an autonomous judgment.",
  },
];

const TRUST_INDICATORS = ["Privacy-First", "Explainable AI", "Human Oversight", "Real-Time Intelligence"];

export function LandingPage() {
  return (
    <div className="min-h-screen bg-maat-white">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-6 py-6">
        <div className="flex items-center gap-2.5">
          <LogoMark />
          <Wordmark className="text-lg" />
        </div>
        <nav className="flex items-center gap-3">
          <Link to="/login">
            <Button variant="ghost" size="sm">
              Log in
            </Button>
          </Link>
          <Link to="/login">
            <Button variant="primary" size="sm">
              Start Demo
            </Button>
          </Link>
        </nav>
      </header>

      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="bg-grid-faint absolute inset-0 opacity-40" />
        <div className="balance-glow absolute left-1/2 top-0 h-[560px] w-[560px] -translate-x-1/2 rounded-full" />
        <div className="relative mx-auto max-w-4xl px-6 pb-24 pt-16 text-center">
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="inline-flex items-center gap-2 rounded-full border border-charcoal-200 bg-white px-4 py-1.5 text-xs font-medium text-charcoal-600 shadow-sm"
          >
            <span className="size-1.5 rounded-full bg-turquoise-500" />
            Explainable Human Authenticity Intelligence
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.55, delay: 0.05 }}
            className="mt-6 text-4xl font-semibold tracking-tight text-charcoal-900 sm:text-5xl"
          >
            Evidence-Based Human Trust
            <br />
            for Digital Decisions
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.55, delay: 0.1 }}
            className="mx-auto mt-5 max-w-xl text-base text-charcoal-600"
          >
            Transform behavioral signals into transparent decision confidence through explainable AI.
            MAAT continuously evaluates interaction authenticity — the human always makes the final call.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.55, delay: 0.15 }}
            className="mt-8 flex items-center justify-center gap-3"
          >
            <Link to="/login">
              <Button size="lg" className="gap-2">
                Start Demo <ArrowRight className="size-4" />
              </Button>
            </Link>
            <Button variant="secondary" size="lg">
              View Product Overview
            </Button>
          </motion.div>

          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="mt-12 flex flex-wrap items-center justify-center gap-x-8 gap-y-3"
          >
            {TRUST_INDICATORS.map((t) => (
              <span key={t} className="text-xs font-medium tracking-wide text-charcoal-500">
                {t}
              </span>
            ))}
          </motion.div>
        </div>
      </section>

      {/* Capabilities */}
      <section className="mx-auto max-w-6xl px-6 pb-24">
        <div className="mb-10 text-center">
          <p className="text-xs font-semibold uppercase tracking-widest text-gold-600">Core Capabilities</p>
          <h2 className="mt-2 text-2xl font-semibold text-charcoal-900">Capture. Reason. Explain. Support.</h2>
        </div>
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {CAPABILITIES.map(({ icon: Icon, title, body }, i) => (
            <motion.div
              key={title}
              initial={{ opacity: 0, y: 14 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.08 }}
              className="rounded-[var(--radius-card)] border border-charcoal-200 bg-white p-6 shadow-[var(--shadow-card)]"
            >
              <div className="flex size-10 items-center justify-center rounded-full bg-nile-50 text-nile-800">
                <Icon className="size-5" />
              </div>
              <h3 className="mt-4 text-sm font-semibold text-charcoal-800">{title}</h3>
              <p className="mt-2 text-[13px] leading-relaxed text-charcoal-500">{body}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Privacy statement */}
      <section className="border-t border-charcoal-200 bg-papyrus/40">
        <div className="mx-auto max-w-3xl px-6 py-16 text-center">
          <ShieldCheck className="mx-auto size-8 text-turquoise-600" />
          <h3 className="mt-4 text-xl font-semibold text-charcoal-900">Privacy by design, not an afterthought.</h3>
          <p className="mt-3 text-sm leading-relaxed text-charcoal-600">
            No keyboard content is stored. No microphone recording. No persistent video storage.
            MAAT observes behavioral metadata only — never the content of what is typed or said.
          </p>
        </div>
      </section>

      <footer className="mx-auto flex max-w-6xl items-center justify-between px-6 py-8 text-xs text-charcoal-400">
        <span>© {new Date().getFullYear()} MAAT. Built for the AI Hackathon.</span>
        <span>Evidence supports decisions. Humans make them.</span>
      </footer>
    </div>
  );
}
