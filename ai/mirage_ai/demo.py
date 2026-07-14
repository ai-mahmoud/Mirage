"""Deterministic scripted dataset for demo=true sessions and as an offline
fallback if live tracking is unstable during the pitch (MVP Bible, "Demo
Flow" + "prepare a validated demo dataset as fallback").

Timeline (relative to session start):
  0s   - 40s   natural baseline behavior (varied mouse/typing/click/scroll)
  40s  - 55s   two brief tab-switch blips (attention signal shift)
  40s  - 100s  a "mouse jiggler" takes over: near-constant-speed, low-entropy,
               high-reversal cursor motion and no typing — the scripted event
               that should visibly drop Trust DNA and produce evidence cards.

All timestamps returned are absolute epoch-ms (started_at + offset), matching
what a real client would send.
"""

from __future__ import annotations

import math
import random

from .schemas import EventType, RawEvent

JIGGLE_START_MS = 40_000.0
JIGGLE_END_MS = 100_000.0


def _natural_mouse(rng: random.Random, t0: float, t1: float) -> list[RawEvent]:
    """_natural_mouse: Random Number Number -> (list-of RawEvent)
    Purpose: human-like mouse_move events from t0 to t1 — a random walk
    toward shifting targets, with varied step size, angle jitter, and
    inter-sample timing (high entropy/curvature, non-constant speed).
    """
    events: list[RawEvent] = []
    t = t0
    x, y = 640.0, 400.0
    target_x, target_y = x, y
    while t < t1:
        if abs(x - target_x) < 4 and abs(y - target_y) < 4:
            target_x = rng.uniform(80, 1200)
            target_y = rng.uniform(80, 700)
        angle = math.atan2(target_y - y, target_x - x) + rng.uniform(-0.35, 0.35)
        step = rng.uniform(6, 40)
        x += math.cos(angle) * step
        y += math.sin(angle) * step
        dt = rng.uniform(60, 220)
        t += dt
        events.append(RawEvent(type=EventType.mouse_move, t=t, x=round(x, 1), y=round(y, 1)))
    return events


def _jiggler_mouse(rng: random.Random, t0: float, t1: float) -> list[RawEvent]:
    """_jiggler_mouse: Random Number Number -> (list-of RawEvent)
    Purpose: the scripted "mouse jiggler" event — a fixed-period back-and-
    forth oscillation along one axis (near-zero speed variability,
    near-zero direction entropy, near-total reversal rate), the opposite
    of _natural_mouse on every one of those features.
    """
    events: list[RawEvent] = []
    t = t0
    x, y = 640.0, 400.0
    direction = 1
    while t < t1:
        x += 14.0 * direction + rng.uniform(-0.4, 0.4)
        direction *= -1
        t += 100.0
        events.append(RawEvent(type=EventType.mouse_move, t=t, x=round(x, 1), y=round(y, 1)))
    return events


def _natural_typing(rng: random.Random, t0: float, t1: float) -> list[RawEvent]:
    events: list[RawEvent] = []
    t = t0
    while t < t1:
        burst_len = rng.randint(8, 20)
        for _ in range(burst_len):
            t += max(40.0, rng.gauss(150, 60))
            if t >= t1:
                break
            events.append(RawEvent(type=EventType.key_down, t=t))
        t += rng.uniform(2_500, 7_000)
    return events


def _natural_clicks(rng: random.Random, t0: float, t1: float) -> list[RawEvent]:
    events: list[RawEvent] = []
    t = t0
    while t < t1:
        t += rng.uniform(4_000, 9_000)
        if t < t1:
            events.append(RawEvent(type=EventType.mouse_click, t=t))
    return events


def _natural_scrolls(rng: random.Random, t0: float, t1: float) -> list[RawEvent]:
    events: list[RawEvent] = []
    t = t0
    while t < t1:
        t += rng.uniform(3_000, 8_000)
        if t < t1:
            events.append(RawEvent(type=EventType.scroll, t=t, dy=rng.choice([-1, 1]) * rng.uniform(40, 200)))
    return events


def generate_demo_events(started_at: float, seed: int | None = None) -> list[RawEvent]:
    """generate_demo_events: Number [Number] -> (list-of RawEvent)
    Purpose: the full scripted timeline (see module docstring) as
    absolute-epoch-ms RawEvents, sorted by time, ready to feed to
    SessionEngine.ingest via SessionEngine._pull_demo_events. Deterministic:
    the same (started_at, seed) always produces the same events.
    """
    rng = random.Random(seed if seed is not None else 1234)
    events: list[RawEvent] = []

    baseline_end = started_at + JIGGLE_START_MS
    jiggle_end = started_at + JIGGLE_END_MS

    events += _natural_mouse(rng, started_at, baseline_end)
    events += _natural_typing(rng, started_at, baseline_end)
    events += _natural_clicks(rng, started_at, baseline_end)
    events += _natural_scrolls(rng, started_at, baseline_end)

    events += _jiggler_mouse(rng, baseline_end, jiggle_end)

    blip_a = started_at + JIGGLE_START_MS + 3_000
    blip_b = blip_a + 1_500
    blip_c = started_at + JIGGLE_START_MS + 12_000
    blip_d = blip_c + 1_800
    events.append(RawEvent(type=EventType.focus_lost, t=blip_a))
    events.append(RawEvent(type=EventType.visibility_hidden, t=blip_a))
    events.append(RawEvent(type=EventType.visibility_visible, t=blip_b))
    events.append(RawEvent(type=EventType.focus_gained, t=blip_b))
    events.append(RawEvent(type=EventType.focus_lost, t=blip_c))
    events.append(RawEvent(type=EventType.visibility_hidden, t=blip_c))
    events.append(RawEvent(type=EventType.visibility_visible, t=blip_d))
    events.append(RawEvent(type=EventType.focus_gained, t=blip_d))

    events.sort(key=lambda e: e.t)
    return events
