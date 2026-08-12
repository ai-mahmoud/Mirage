"""Deterministic demo-history seeding for the in-memory session store.

Run once at process startup (see api.py's startup hook) so a fresh ai/
instance already has a realistic-looking week of sessions before any
client asks for them — no real-time waiting needed, since each session is
played out via explicit `now` timestamps rather than the wall clock.

backend/'s own seed script (backend/scripts/seed_demo_data.py) mirrors
these sessions into its database afterward, over the same HttpAiClient
proxy the real runtime uses. It discovers the full id/identity list via
`GET /seed/sessions` (see api.py) rather than duplicating PROFILES here —
this module is the single source of truth for what gets seeded.

Trust score honesty note: the synthetic "natural" behavior generator
(demo.py's _natural_*) caps out around a Trust DNA overall of ~65-73 —
it's calibrated to look like decent, unremarkable human behavior, not
flawless behavior, so it never lands in the "high"/"very-high" bands.
Rather than fabricate numbers to force full band coverage, the profile
mix below only claims the bands the engine can genuinely produce
(moderate, low, very-low) — see PROFILES_SUMMARY in this module's tests.
"""

from __future__ import annotations

import random
import time

from .demo import _natural_clicks, _natural_mouse, _natural_scrolls, _natural_typing
from .engine import SessionEngine

CANDIDATE_POOL = [
    ("Amara Osei", "Backend Engineer", "Engineering"),
    ("Diego Fernandez", "Frontend Engineer", "Engineering"),
    ("Mei Lin Tan", "Data Analyst", "Data"),
    ("Samuel Okafor", "Product Manager", "Product"),
    ("Nour El-Sayed", "Site Reliability Engineer", "Engineering"),
    ("Elena Popescu", "UX Designer", "Design"),
    ("Wei Zhang", "Data Scientist", "Data"),
    ("Fatima Khan", "QA Engineer", "Engineering"),
    ("Lucas Silva", "DevOps Engineer", "Engineering"),
    ("Aisha Bello", "Marketing Manager", "Marketing"),
    ("Tom Novak", "Sales Engineer", "Sales"),
    ("Priya Nair", "Mobile Engineer", "Engineering"),
    ("Kwame Mensah", "Security Engineer", "Engineering"),
    ("Sofia Rossi", "Product Designer", "Design"),
    ("Ahmed Hassan", "Engineering Manager", "Engineering"),
]
INTERVIEW_TYPES = ["Technical Interview", "Screening Call", "Panel Interview", "Portfolio Review"]
OBSERVERS = ["Priya Raman", "Jordan Blake", "Sam Whitfield", "Alonso Reyes"]

# (key, demo_mode, duration_ms) — duration for "clean" is how long natural
# behavior runs; for jiggler archetypes it's when the session gets
# finalized (empirically chosen — see the module docstring).
ARCHETYPES = [
    ("clean_short", False, 60_000.0),
    ("clean_medium", False, 130_000.0),
    ("clean_long", False, 200_000.0),
    ("brief_dip", True, 55_000.0),
    ("moderate_flag", True, 130_000.0),
    ("severe_flag", True, 92_000.0),
]

# Monday-heavy, weekend-light — just enough shape that the Daily Sessions
# chart doesn't look perfectly flat. Values are relative weights, not counts.
DAY_WEIGHTS = [9, 8, 7, 6, 5, 3, 2]

TOTAL_SESSIONS = 45


def _day_sequence() -> list[int]:
    """_day_sequence: -> (list-of Number)
    Purpose: a deterministic sequence of "days ago" values (0 = today),
    weighted per DAY_WEIGHTS, cycled to cover TOTAL_SESSIONS.
    """
    days: list[int] = []
    for day, weight in enumerate(DAY_WEIGHTS):
        days += [day] * weight
    return days


def build_profiles(total: int = TOTAL_SESSIONS) -> list[dict]:
    """build_profiles: [Number] -> (list-of dict)
    Purpose: deterministically generate `total` session profiles — one
    "live" (today, never finalized), the rest ended, cycling through the
    candidate pool and archetypes so repeat candidates and varied outcomes
    both occur, matching a real hiring pipeline. Each dict has:
    session_id, candidate, position, department, interview_type, observer,
    days_ago, archetype, demo_mode, duration_ms, seed.
    """
    days = _day_sequence()
    profiles: list[dict] = []

    profiles.append(
        {
            "session_id": "seed-000",
            "candidate": CANDIDATE_POOL[0][0],
            "position": CANDIDATE_POOL[0][1],
            "department": CANDIDATE_POOL[0][2],
            "interview_type": INTERVIEW_TYPES[0],
            "observer": OBSERVERS[0],
            "days_ago": 0,
            "archetype": "live",
            "demo_mode": False,
            "duration_ms": 45_000.0,
            "seed": 1,
            "live": True,
        }
    )

    for i in range(1, total):
        candidate, position, department = CANDIDATE_POOL[i % len(CANDIDATE_POOL)]
        archetype_key, demo_mode, duration_ms = ARCHETYPES[i % len(ARCHETYPES)]
        profiles.append(
            {
                "session_id": f"seed-{i:03d}",
                "candidate": candidate,
                "position": position,
                "department": department,
                "interview_type": INTERVIEW_TYPES[i % len(INTERVIEW_TYPES)],
                "observer": OBSERVERS[i % len(OBSERVERS)],
                "days_ago": days[i % len(days)],
                "archetype": archetype_key,
                "demo_mode": demo_mode,
                "duration_ms": duration_ms,
                "seed": 100 + i,
                "live": False,
            }
        )
    return profiles


PROFILES = build_profiles()


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


def _play_out(profile: dict, started_at_ms: float) -> SessionEngine:
    """_play_out: dict Number -> SessionEngine
    Purpose: build and tick one profile's engine forward through simulated
    time (never real wall-clock), finalizing it unless it's the live one.
    """
    engine = SessionEngine(
        session_id=profile["session_id"],
        candidate_name=profile["candidate"],
        observer_name=profile["observer"],
        position=profile["position"],
        department=profile["department"],
        interview_type=profile["interview_type"],
        demo_mode=profile["demo_mode"],
        seed=profile["seed"],
        started_at=started_at_ms,
    )
    if not profile["demo_mode"]:
        engine.ingest(_natural_only_events(started_at_ms, profile["duration_ms"], profile["seed"]))

    for t in range(1_000, int(profile["duration_ms"]), 1_000):
        engine.tick(started_at_ms + t)

    if not profile["live"]:
        engine.finalize(started_at_ms + profile["duration_ms"])

    return engine


def seed_sessions(sessions: dict[str, SessionEngine]) -> None:
    """seed_sessions: (dict String -> SessionEngine) -> Void
    Purpose: populate `sessions` (the api module's live session store) with
    PROFILES, unless it already has something in it (idempotent — safe to
    call on every process start; never overwrites real sessions).
    """
    if sessions:
        return

    now = time.time() * 1000.0
    for profile in PROFILES:
        started_at_ms = now - profile["days_ago"] * 86_400_000.0 - 3_600_000.0
        sessions[profile["session_id"]] = _play_out(profile, started_at_ms)
