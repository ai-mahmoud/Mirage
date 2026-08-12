import { motion, type Variants } from "framer-motion";
import { Link } from "react-router-dom";
import { Feather, Scale, Eye, ShieldCheck, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { LogoMark, Wordmark } from "@/components/shared/logo-mark";
import { BalanceSignature } from "@/features/landing/balance-signature";

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

const fadeUp: Variants = {
  hidden: { opacity: 0, y: 18 },
  show: (i: number = 0) => ({
    opacity: 1,
    y: 0,
    transition: { duration: 0.6, delay: i * 0.08, ease: [0.16, 1, 0.3, 1] as const },
  }),
};

export function LandingPage() {
  return (
    <div className="min-h-screen bg-maat-white">
      {/* Nav */}
      <header className="sticky top-0 z-20 border-b border-transparent bg-maat-white/70 backdrop-blur-md">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
          <div className="flex items-center gap-2.5">
            <LogoMark />
            <Wordmark className="text-lg" />
          </div>
          <nav className="flex items-center gap-2">
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
        </div>
      </header>

      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="bg-grid-faint absolute inset-0 opacity-[0.35] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,black,transparent)]" />
        <div className="balance-glow absolute left-1/2 top-[-120px] h-[620px] w-[620px] -translate-x-1/2 rounded-full" />

        <div className="relative mx-auto max-w-4xl px-6 pb-8 pt-20 text-center sm:pt-28">
          <motion.div
            variants={fadeUp}
            initial="hidden"
            animate="show"
            custom={0}
            className="inline-flex items-center gap-2 rounded-full border border-charcoal-200 bg-white px-4 py-1.5 text-xs font-medium text-charcoal-600 shadow-sm"
          >
            <span className="relative flex size-1.5">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-turquoise-400 opacity-75" />
              <span className="relative inline-flex size-1.5 rounded-full bg-turquoise-500" />
            </span>
            Explainable Human Authenticity Intelligence
          </motion.div>

          <motion.h1
            variants={fadeUp}
            initial="hidden"
            animate="show"
            custom={1}
            className="text-balance mt-7 text-[2.75rem] font-semibold leading-[1.08] tracking-[-0.02em] text-charcoal-900 sm:text-6xl sm:leading-[1.05]"
          >
            Evidence-based human trust
            <br />
            <span className="bg-gradient-to-r from-nile-900 via-nile-700 to-turquoise-600 bg-clip-text text-transparent">
              for digital decisions.
            </span>
          </motion.h1>

          <motion.p
            variants={fadeUp}
            initial="hidden"
            animate="show"
            custom={2}
            className="text-balance mx-auto mt-6 max-w-xl text-[17px] leading-relaxed text-charcoal-500"
          >
            MAAT transforms behavioral signals into transparent decision confidence through explainable AI —
            continuously evaluating interaction authenticity while the human always makes the final call.
          </motion.p>

          <motion.div
            variants={fadeUp}
            initial="hidden"
            animate="show"
            custom={3}
            className="mt-9 flex flex-col items-center justify-center gap-3 sm:flex-row"
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
            variants={fadeUp}
            initial="hidden"
            animate="show"
            custom={4}
            className="mt-14 flex flex-wrap items-center justify-center gap-x-9 gap-y-3"
          >
            {TRUST_INDICATORS.map((t) => (
              <span key={t} className="flex items-center gap-1.5 text-xs font-medium tracking-wide text-charcoal-400">
                <span className="size-1 rounded-full bg-gold-500" />
                {t}
              </span>
            ))}
          </motion.div>
        </div>

        {/* Signature element — the weighing of evidence, rendered as a live balance */}
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.5, ease: [0.16, 1, 0.3, 1] }}
          className="relative mx-auto mt-16 max-w-3xl px-6 pb-24"
        >
          <BalanceSignature />
        </motion.div>
      </section>

      {/* Capabilities */}
      <section className="mx-auto max-w-6xl px-6 pb-28">
        <div className="mb-14 text-center">
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-gold-600">Core Capabilities</p>
          <h2 className="mt-3 text-[26px] font-semibold tracking-tight text-charcoal-900">
            Capture. Reason. Explain. Support.
          </h2>
        </div>
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {CAPABILITIES.map(({ icon: Icon, title, body }, i) => (
            <motion.div
              key={title}
              initial={{ opacity: 0, y: 18 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-60px" }}
              transition={{ delay: i * 0.09, duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
              className="card-hover group rounded-[var(--radius-card)] border border-charcoal-200 bg-white p-6"
            >
              <div className="flex size-11 items-center justify-center rounded-full bg-nile-50 text-nile-800 transition-colors duration-300 group-hover:bg-nile-900 group-hover:text-white">
                <Icon className="size-5" />
              </div>
              <h3 className="mt-5 text-[15px] font-semibold text-charcoal-800">{title}</h3>
              <p className="mt-2 text-[13px] leading-relaxed text-charcoal-500">{body}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Privacy statement */}
      <section className="border-t border-charcoal-200 bg-papyrus/40">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="mx-auto max-w-3xl px-6 py-20 text-center"
        >
          <div className="mx-auto flex size-12 items-center justify-center rounded-full bg-turquoise-100">
            <ShieldCheck className="size-6 text-turquoise-700" />
          </div>
          <h3 className="mt-5 text-2xl font-semibold tracking-tight text-charcoal-900">
            Privacy by design, not an afterthought.
          </h3>
          <p className="mx-auto mt-4 max-w-lg text-[15px] leading-relaxed text-charcoal-600">
            No keyboard content is stored. No microphone recording. No persistent video storage.
            MAAT observes behavioral metadata only — never the content of what is typed or said.
          </p>
        </motion.div>
      </section>

      <footer className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-3 px-6 py-10 text-xs text-charcoal-400 sm:flex-row">
        <span>© {new Date().getFullYear()} MAAT. Built for the AI Hackathon.</span>
        <span className="italic text-charcoal-400">Evidence supports decisions. Humans make them.</span>
      </footer>
    </div>
  );
}
