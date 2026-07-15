"""Deterministic demo-history seeding for the in-memory session store.

Run once at process startup (see api.py's startup hook) so a fresh ai/
instance already has a handful of realistic finished sessions before any
client asks for them — no real-time waiting needed, since each session is
played out via explicit `now` timestamps rather than the wall clock.

backend/'s own seed script (backend/scripts/seed_demo_data.py) mirrors
these sessions into its database afterward, over the same HttpAiClient
proxy the real runtime uses — it does not import this module. Its
PROFILES list must reference the same session ids as this one.
"""

from __future__ import annotations

import random
import time

from .demo import _natural_clicks, _natural_mouse, _natural_scrolls, _natural_typing
from .engine import SessionEngine

# (session_id, candidate, position, department, interview_type, observer, days_ago, outcome)
# outcome: "clean" (natural behavior only), "flagged" (scripted mouse-jiggler
# event triggers manual review), "live" (still in progress, never finalized).
PROFILES = [
    ("seed-amara-osei", "Amara Osei", "Backend Engineer", "Engineering", "Technical Interview", "Priya Raman", 4, "clean"),
    ("seed-diego-fernandez", "Diego Fernandez", "Frontend Engineer", "Engineering", "Technical Interview", "Priya Raman", 3, "clean"),
    ("seed-mei-lin-tan", "Mei Lin Tan", "Data Analyst", "Data", "Screening Call", "Jordan Blake", 2, "flagged"),
    ("seed-samuel-okafor", "Samuel Okafor", "Product Manager", "Product", "Panel Interview", "Jordan Blake", 1, "clean"),
    ("seed-nour-el-sayed", "Nour El-Sayed", "Site Reliability Engineer", "Engineering", "Technical Interview", "Priya Raman", 1, "flagged"),
    ("seed-elena-popescu", "Elena Popescu", "UX Designer", "Design", "Portfolio Review", "Jordan Blake", 0, "live"),
]


def _natural_only_events(started_at_ms: float, duration_ms: float, seed: int):
    """A full session of ONLY natural behavior (no jiggler) — reuses the
    demo module's own generators, so a "clean" seed session is produced by
    the exact same code path a real, uneventful interview would hit."""
    rng = random.Random(seed)
    end = started_at_ms + duration_ms
    events = (
        _natural_mouse(rng, started_at_ms, end)
        + _natural_typing(rng, started_at_ms, end)
        + _natural_clicks(rng, started_at_ms, end)
        + _natural_scrolls(rng, started_at_ms, end)
    )
    events.sort(key=lambda e: e.t)
    return events


def seed_sessions(sessions: dict[str, SessionEngine]) -> None:
    """seed_sessions: (dict String -> SessionEngine) -> Void
    Purpose: populate `sessions` (the api module's live session store) with
    PROFILES, unless it already has something in it (idempotent — safe to
    call on every process start; never overwrites real sessions).
    """
    if sessions:
        return

    now = time.time() * 1000.0
    for i, (session_id, candidate, position, department, interview_type, observer, days_ago, outcome) in enumerate(
        PROFILES
    ):
        started_at_ms = now - days_ago * 86_400_000.0 - 3_600_000.0
        if outcome == "live":
            duration_ms = 45_000.0
        elif outcome == "flagged":
            duration_ms = 92_000.0  # ends mid-jiggler (40s-100s), while still clearly degraded
        else:
            duration_ms = 130_000.0
        demo_mode = outcome == "flagged"

        engine = SessionEngine(
            session_id=session_id,
            candidate_name=candidate,
            observer_name=observer,
            position=position,
            department=department,
            interview_type=interview_type,
            demo_mode=demo_mode,
            seed=100 + i,
            started_at=started_at_ms,
        )
        if not demo_mode:
            engine.ingest(_natural_only_events(started_at_ms, duration_ms, 100 + i))

        for t in range(1_000, int(duration_ms), 1_000):
            engine.tick(started_at_ms + t)

        if outcome != "live":
            engine.finalize(started_at_ms + duration_ms)

        sessions[session_id] = engine
