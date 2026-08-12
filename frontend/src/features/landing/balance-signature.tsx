import { motion } from "framer-motion";

const LEFT_LABELS = ["Cursor Entropy", "Typing Rhythm", "Focus Stability"];
const RIGHT_LABELS = ["Context Integrity", "Idle Recovery", "Response Latency"];

export function BalanceSignature() {
  return (
    <div className="relative rounded-[24px] border border-charcoal-200 bg-white/70 px-8 py-10 shadow-[var(--shadow-float)] backdrop-blur-sm sm:px-14">
      <p className="text-center text-[11px] font-medium uppercase tracking-[0.16em] text-charcoal-400">
        Multiple signals, weighed together
      </p>

      <div className="relative mt-8 flex items-end justify-center gap-0">
        {/* Left pan */}
        <div className="flex w-40 flex-col items-center gap-2 sm:w-52">
          {LEFT_LABELS.map((label, i) => (
            <motion.span
              key={label}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.9 + i * 0.12, duration: 0.4 }}
              className="rounded-full bg-nile-50 px-3 py-1 text-[11px] font-medium text-nile-800"
            >
              {label}
            </motion.span>
          ))}
          <motion.div
            initial={{ y: 0 }}
            animate={{ y: [0, 6, 0] }}
            transition={{ duration: 4.5, repeat: Infinity, ease: "easeInOut" }}
            className="mt-2 h-px w-full origin-right bg-charcoal-200"
          />
        </div>

        {/* Fulcrum */}
        <div className="relative mx-3 flex flex-col items-center sm:mx-6">
          <motion.div
            initial={{ scale: 0.6, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.6, duration: 0.5 }}
            className="flex size-14 items-center justify-center rounded-full bg-gold-500 shadow-lg shadow-gold-500/30"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path d="M12 2v20M6 8h12" stroke="#0a1c33" strokeWidth="1.8" strokeLinecap="round" />
            </svg>
          </motion.div>
          <div className="h-16 w-px bg-charcoal-200 sm:h-20" />
        </div>

        {/* Right pan */}
        <div className="flex w-40 flex-col items-center gap-2 sm:w-52">
          {RIGHT_LABELS.map((label, i) => (
            <motion.span
              key={label}
              initial={{ opacity: 0, x: 8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.9 + i * 0.12, duration: 0.4 }}
              className="rounded-full bg-turquoise-100 px-3 py-1 text-[11px] font-medium text-turquoise-700"
            >
              {label}
            </motion.span>
          ))}
          <motion.div
            initial={{ y: 0 }}
            animate={{ y: [0, -6, 0] }}
            transition={{ duration: 4.5, repeat: Infinity, ease: "easeInOut" }}
            className="mt-2 h-px w-full origin-left bg-charcoal-200"
          />
        </div>
      </div>

      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.4, duration: 0.5 }}
        className="mt-8 text-center text-sm text-charcoal-500"
      >
        Evidence never rests on a single signal —{" "}
        <span className="font-medium text-charcoal-700">balance produces confidence.</span>
      </motion.p>
    </div>
  );
}
