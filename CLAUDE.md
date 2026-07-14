# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository State

This is a greenfield hackathon project. There is **no code yet** — the only artifact is `MVP BIBLE.docx`, the authoritative product/engineering spec. The repo is not yet a git repository. There are no build, lint, or test commands until a stack is scaffolded; add them here when that happens.

To read the spec (binary .docx, cannot be read directly):

```bash
unzip -p "MVP BIBLE.docx" word/document.xml | python3 -c "
import sys, re, html
xml = sys.stdin.read()
xml = re.sub(r'</w:p>', '\n', xml)
print(html.unescape(re.sub(r'<[^>]+>', '', xml)))"
```

## What This Product Is

An **explainable behavioral intelligence platform** for AI-assisted remote hiring verification. During an online interview, it collects privacy-preserving behavioral signals (mouse dynamics, keyboard timing, window focus, idle patterns — never keystroke content, audio, or video), transforms them into explainable evidence, and gives the HR interviewer a confidence-calibrated recommendation. The AI assists; the human decides. Target: a flawless 3-minute demo for hackathon judges.

## Non-Negotiable Product Principles

Every feature and code decision must comply with these (from the "Project Constitution"):

1. **Evidence before conclusions** — evidence is always displayed/generated before any recommendation.
2. **Human oversight** — the system never makes hiring decisions; recommendations are conservative ("Manual Review Recommended", never "Reject Candidate" or "Cheating Detected").
3. **Privacy by design** — no keystroke content, no clipboard, no audio, no persistent video. Only interaction metadata.
4. **Explainability** — every recommendation references its supporting evidence; every Trust DNA update is explainable.
5. **Multi-signal reasoning** — no conclusion may rest on a single signal; conflicting evidence lowers confidence rather than forcing a verdict.
6. **Simplicity** — if a feature doesn't strengthen the 3-minute demo, don't build it.

Language rule: never surface accusatory or technical-AI phrasing to users. Say "Behavioral inconsistency detected", not "Fake user detected".

## Architecture (AI Pipeline)

The core is a staged evidence-synthesis pipeline. Each stage lifts raw observations into higher-level semantics:

```
Signal Collection → Feature Engineering → Behavior Intelligence Engine
→ Evidence Reasoning Engine → Trust DNA Generator → Decision Confidence Engine
→ Human Recommendation Layer
```

- **Signals** (15 defined, SIG-001…SIG-015): cursor velocity/entropy/curvature, click & typing rhythm, pause distribution, idle recovery, window focus, browser visibility, response latency, interaction density, scroll dynamics, plus derived signals (behavioral stability, attention drift, context continuity). Each has a reliability grade A+–D; low-grade signals (e.g. browser visibility = C) must never independently drive recommendations.
- **Trust DNA** replaces a single trust score: six independently-evolving dimensions — Behavioral Consistency (25%), Interaction Naturalness (20%), Attention Stability (20%), Context Integrity (15%), Adaptive Responsiveness (10%), Session Authenticity synthesis (10%). Weights are configurable heuristics, not constants.
- **Evidence Reasoning Engine**: aggregates signals → correlates concurrent changes → weights by reliability → synthesizes human-readable evidence cards (title, description, severity, confidence, timestamp).
- **Confidence is dual-track**: Evidence Confidence and Recommendation Confidence are computed and displayed separately.
- **Missing data policy**: single missing signal → ignore; several missing → reduce confidence; critical signal missing → "Insufficient Evidence". Never fabricate evidence.
- MVP AI is **rule-based/deterministic** (calibrated heuristics), architected so real models can slot in later.

Signals follow a unified metadata schema: `{signalId, category, timestamp, value, normalizedValue, confidence, reliability, source, context}`.

## Application Structure

Exactly **four screens**, one continuous journey (Landing → Login → Dashboard → Create Session → Live Session → Report → Export):

1. **Landing** — value prop in <8s; CTA "Start Demo".
2. **Dashboard** — KPI cards, engine status, activity feed; CTA "Start Behavioral Session". Demo login: `demo@platform.ai`.
3. **Live Session** — ~70% of the judging experience. Layout: session header / Trust DNA + Timeline + Evidence Feed / Live Signals + Recommendation Panel. Always-visible privacy card. Everything updates live (dashboard latency < 1s, signal stream every second).
4. **Session Report** — executive summary, Trust DNA bars, evidence table, recommendation, privacy summary. Export: PDF only (CSV/JSON buttons disabled).

Demo flow includes a scripted "behavior event" (e.g. mouse jiggler) that visibly drops Trust DNA, adds evidence cards one by one, then updates the recommendation. Prepare a validated demo dataset as fallback for live-tracking instability.

## Design System (enforced)

Egyptian-philosophy-inspired ("Ma'at" — balance, evidence, truth), but conceptual only — no literal pyramids/hieroglyphs.

- **Colors**: Nile Blue `#123C69` (primary/nav), Ma'at White `#FAFAF8` (cards), Papyrus Sand `#F3E9D2` (backgrounds), Horus Gold `#D4AF37` (verified evidence only, ≤5% of UI), Lotus Turquoise `#2A9D8F` (interactive/progress), Granite Charcoal `#2B2B2B` (text), Emerald `#2E8B57` (trusted), Amber `#E9A03B` (needs review), Obsidian Red `#A63D40` (manual review required).
- **Typography**: Inter (primary), IBM Plex Sans (tables/reports). Weights 300–700.
- **Spacing**: 8-point grid only (8/16/24/32/48/64/96). Radii: cards 16px, buttons 14px, inputs 12px, badges 999px.
- **Icons**: outline style only, never filled. Symbolic mapping: feather = evidence, scale = confidence, papyrus scroll = session.
- **Motion**: fade/slide/progress/count-up/morph/glow allowed; bounce/shake/rotate/flash/confetti forbidden. Hover 120ms, cards 220ms, pages 300ms. AI processing shown as flowing particles/waves, never spinners.
- **UX rules**: one primary action per screen; max three clicks to any feature; button labels are specific verbs ("Start Session", "Generate Report" — never "Submit"/"Continue"); every card answers exactly one question, max height 320px; color is never the sole status indicator; WCAG AA contrast; 44×44px touch targets.

## Out of Scope (do not build)

Multi-user/org management, billing, notifications, historical analytics, face/voice/deepfake recognition, video analysis, mobile/native apps, integrations, multi-language. Chrome-only for the MVP.
