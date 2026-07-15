# MAAT — Explainable Human Authenticity Intelligence

Hackathon MVP frontend. Transforms behavioral evidence into explainable decision
confidence for AI-assisted remote hiring verification.

## Stack

React 19 · TypeScript · Vite · Tailwind CSS v4 · Framer Motion · React Router ·
Recharts · Lucide React · React Hook Form + Zod · TanStack Query

## Getting started

```bash
npm install
npm run dev
```

Open `http://localhost:5173`. Log in with the pre-filled demo credentials
(`demo@platform.ai`) — one click, no setup required.

## Structure

```
src/
  app/            App root, providers
  router/         Route table
  layouts/        Dashboard / Auth shells
  features/       One folder per screen (landing, auth, dashboard,
                   live-session, trust-dna, evidence, timeline,
                   recommendations, reports, privacy, settings)
  components/
    ui/           Design-system primitives (Button, Card, Badge, Input, Progress)
    dashboard/    Domain components (Trust DNA, Evidence Feed, Timeline,
                   Recommendation Panel, Live Signals, Privacy Card)
    shared/       Sidebar, Topbar, Logo
  contexts/       Auth context (demo session)
  data/           Demo dataset — clearly marked, no real candidate data
  lib/            cn(), formatting helpers, confidence/band mappings
  types/          Domain model (Trust DNA, Evidence, Recommendation, Session…)
```

## Design system

Tokens live in `src/index.css` under `@theme`. Palette, radii, and shadows follow
the MAAT Design System spec (Nile Blue, Ma'at White, Papyrus Sand, Horus Gold,
Lotus Turquoise, Granite Charcoal, Emerald/Amber/Crimson status colors).

## Screens

Four primary screens per the Information Architecture: Dashboard, Live Session,
Session Report, plus supporting Trust DNA / Evidence / Timeline / Recommendations
detail views and a Privacy Center. All data is static demo data — no live
tracking, backend, or persistence is wired up in this MVP frontend.
