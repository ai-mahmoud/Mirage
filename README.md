# Mirage: Explainable Behavioral Intelligence Platform

[![Hackathon Project](https://img.shields.io/badge/project-hackathon-brightgreen.svg)](https://github.com/ai-mahmoud/Mirage)
[![Built with Python](https://img.shields.io/badge/language-Python-3776ab.svg)](https://www.python.org/)
[![Privacy First](https://img.shields.io/badge/privacy-first-blue.svg)](#privacy-by-design)

## Overview

**Mirage** is an AI-assisted behavioral intelligence platform for remote hiring verification. During online interviews, it collects privacy-preserving behavioral signals (mouse dynamics, keyboard timing, window focus, idle patterns) and transforms them into explainable evidence to help HR interviewers make informed hiring decisions.

The system is **human-centric**: the AI assists through evidence and recommendations, but humans retain full decision-making authority. Every insight is calibrated with confidence scores and backed by transparent evidence.

### Core Vision

> *Evidence before conclusions. Privacy by default. Transparency always. Humans decide.*

---

## Features

### 🎯 Behavioral Signal Collection (15 Signals)

Mirage monitors **interaction metadata only**—never keystroke content, clipboard, audio, or video:

- **Cursor Dynamics**: velocity, entropy, curvature
- **Typing Patterns**: click rhythm, keystroke timing, pause distribution
- **Session Behavior**: idle recovery, window focus, browser visibility
- **Attention Metrics**: response latency, interaction density, scroll dynamics
- **Derived Signals**: behavioral stability, attention drift, context continuity

Each signal includes metadata: `{signalId, category, timestamp, value, normalizedValue, confidence, reliability, source, context}`

### 🧬 Trust DNA Engine

A **multi-dimensional trust model** replaces single-score systems:

| Dimension | Weight | Purpose |
|-----------|--------|---------|
| Behavioral Consistency | 25% | Pattern recognition across interactions |
| Interaction Naturalness | 20% | Detects scripted or automated behavior |
| Attention Stability | 20% | Monitors focus and engagement changes |
| Context Integrity | 15% | Validates session environment consistency |
| Adaptive Responsiveness | 10% | Tracks real-time behavior adjustments |
| Session Authenticity | 10% | Overall coherence synthesis |

**Weights are configurable heuristics**—architected for future ML model integration.

### 🔍 Evidence Reasoning Engine

- **Signal Aggregation**: combines multi-source observations
- **Correlation Detection**: identifies concurrent behavioral changes
- **Reliability Weighting**: down-weights low-confidence signals (e.g., browser visibility = Grade C)
- **Evidence Cards**: generates human-readable insights with severity, confidence, and timestamps
- **Dual Confidence Tracking**: Evidence Confidence and Recommendation Confidence computed separately

### 🎨 Four-Screen UX Journey

1. **Landing Screen** — 8-second value proposition, "Start Demo" CTA
2. **Dashboard** — KPI cards, engine status, activity feed, session creation
3. **Live Session** — 70% of demo experience
   - Trust DNA visualization + timeline
   - Live evidence feed + signals panel
   - Recommendation panel with calibrated confidence
   - Always-visible privacy compliance card
   - <1s dashboard latency, 1/sec signal stream updates
4. **Session Report** — Executive summary with Trust DNA bars, evidence table, PDF export only

### 🔐 Privacy by Design

- ✅ **Collected**: mouse/keyboard interaction timing, window focus, scrolling, page visibility
- ❌ **Never Collected**: keystroke content, clipboard data, audio, video, biometric data
- ❌ **Never Stored Persistently**: only session-scoped, real-time analysis
- Transparent privacy card always visible during live sessions

---

## Non-Negotiable Principles

Every line of code must comply with the **Project Constitution**:

1. **Evidence Before Conclusions** — all evidence displayed before recommendations
2. **Human Oversight** — no autonomous hiring decisions; conservative language only ("Manual Review Recommended", never "Reject" or "Cheating Detected")
3. **Privacy by Design** — interaction metadata only; no keystroke logging, audio, or video
4. **Explainability** — every recommendation links to supporting evidence; Trust DNA updates are transparent
5. **Multi-Signal Reasoning** — no single signal drives a conclusion; conflicting signals reduce confidence, not force verdicts
6. **Simplicity** — features must strengthen the 3-minute demo; scope ruthlessly

**Language Rule**: Use behavioral language, not accusatory. Say *"Behavioral inconsistency detected"*, not *"Fake user detected"*.

---

## Architecture

### AI Pipeline (Evidence Synthesis)

```
Signal Collection
       ↓
Feature Engineering
       ↓
Behavior Intelligence Engine
       ↓
Evidence Reasoning Engine
       ↓
Trust DNA Generator
       ↓
Decision Confidence Engine
       ↓
Human Recommendation Layer
```

### Signal Reliability Grades

| Grade | Definition | Use in Recommendations |
|-------|-----------|----------------------|
| A+ | Highly reliable, low variance | Primary evidence |
| A | Reliable, small variance | Primary evidence |
| B | Moderate reliability, some noise | Supporting evidence only |
| C | Low reliability, high variance | Cannot independently drive decisions |
| D | Unreliable, high noise | Ignored or confidence-reducing only |

**Missing Data Policy**:
- Single missing signal → ignore
- Several missing signals → reduce confidence
- Critical signal missing → "Insufficient Evidence"
- **Never** fabricate missing data

### MVP AI Approach

**Rule-based/deterministic** with calibrated heuristics — architected for seamless ML model integration later. No external dependencies on cloud AI services; all reasoning runs client-side.

---

## Design System

Inspired by Egyptian philosophy concepts (**Ma'at**: balance, evidence, truth) — conceptual only, no literal imagery.

### Colors

| Color | Hex | Usage |
|-------|-----|-------|
| Nile Blue | `#123C69` | Primary, navigation, headings |
| Ma'at White | `#FAFAF8` | Card backgrounds, text surfaces |
| Papyrus Sand | `#F3E9D2` | Page backgrounds, gentle contrast |
| Horus Gold | `#D4AF37` | Verified evidence only (≤5% of UI) |
| Lotus Turquoise | `#4DB8C4` | Status indicators, valid states |
| Dust Red | `#A85A5A` | Manual review, attention needed (not harsh) |
| Hieroglyph Gray | `#626262` | Secondary text, disabled states |

### Typography

- **Primary**: Inter (300–700 weights)
- **Reports/Tables**: IBM Plex Sans (monospace for data integrity)
- **Baseline**: 16px, line-height 1.5

### Spacing & Radii

- **8-point grid only**: 8, 16, 24, 32, 48, 64, 96px
- **Cards**: 16px radius
- **Buttons**: 14px radius
- **Inputs**: 12px radius
- **Badges**: 999px (full pill)

### Motion

- **Allowed**: fade, slide, progress, count-up, morph, glow, flowing particles
- **Forbidden**: bounce, shake, rotate, flash, confetti
- **Timing**: Hover 120ms, cards 220ms, pages 300ms
- **AI Processing**: flowing particles/waves/morphs (no spinners)

### Icons

- **Style**: Outline only, never filled
- **Mapping**: feather = evidence, scale = confidence, papyrus scroll = session

### UX Rules

- One primary action per screen
- Max 3 clicks to any feature
- Button labels: specific verbs ("Start Session", "Generate Report") — never generic
- Every card answers a single question
- No auto-play; all animations pause on interaction

---

## Quick Start

### Prerequisites

- Python 3.9+
- Chrome browser (MVP Chrome-only)
- No external cloud dependencies

### Project Structure

```
Mirage/
├── README.md                 # This file
├── CLAUDE.md                 # AI development guidance
├── MVP BIBLE.docx            # Authoritative spec (binary)
└── [code to be scaffolded]   # Backend, frontend, tests
```

### Reading the MVP Spec

The authoritative specification is in `MVP BIBLE.docx`. Extract readable text:

```bash
unzip -p "MVP BIBLE.docx" word/document.xml | python3 -c "
import sys, re, html
xml = sys.stdin.read()
xml = re.sub(r'</w:p>', '\n', xml)
print(html.unescape(re.sub(r'<[^>]+>', '', xml)))"
```

### Demo Credentials

- **Username**: `demo@platform.ai`
- **Role**: HR Interviewer

### Demo Flow

1. Login to dashboard
2. Create new behavioral session
3. Observe scripted "behavior event" (e.g., mouse jiggler activity)
4. Watch Trust DNA drop in real-time as evidence cards populate
5. View recommendation with calibrated confidence
6. Generate and export session report (PDF only)

---

## Current Status

🚀 **Greenfield Hackathon Project**

- ✅ Architecture & design system defined
- ✅ 15 signals specified with reliability grades
- ✅ Trust DNA dimensions & weights validated
- ✅ UX journey & 4-screen design finalized
- ✅ Privacy & ethics framework established
- ⏳ **Next**: scaffold tech stack and implement core pipeline

---

## Out of Scope (MVP)

The following are explicitly **not** in scope for the hackathon demo:

- Multi-user / organization management
- Billing & subscription
- Notifications
- Historical analytics
- Face recognition, deepfake detection, voice analysis
- Video analysis
- Mobile or native apps
- Third-party integrations
- Multi-language support
- Browser support beyond Chrome

---

## Contributing

This is a hackathon project under active development. All code must:

1. ✅ Comply with the **Project Constitution** (see principles above)
2. ✅ Include transparent evidence generation before recommendations
3. ✅ Respect privacy by design (no keystroke logging, etc.)
4. ✅ Use the defined design system (colors, typography, spacing, motion)
5. ✅ Keep the 3-minute demo experience flawless

For detailed development guidance, see [CLAUDE.md](CLAUDE.md).

---

## License

[Add license information]

---

## Support & Contact

For questions or clarifications on product vision, architecture, or principles, refer to the [CLAUDE.md](CLAUDE.md) file or the MVP BIBLE specification.

---

**Mirage**: Turning behavioral signals into human-centered hiring intelligence. 🌟
