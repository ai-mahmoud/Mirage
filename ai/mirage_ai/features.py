"""Feature engineering: raw interaction metadata -> numerical features.

Every function is pure and deterministic, consuming only timestamps and
coordinates. Keystroke content never reaches this layer — the event
schema has no field that could carry it.

Each function below follows the How-to-Design-Functions recipe: a
signature comment, a purpose statement, and (for the small pure helpers)
a worked example. The `*_features` functions return `None` when there
isn't enough data to compute a meaningful result — callers must treat a
missing feature as "signal not computable this tick," per the missing-data
policy, not as a zero or a failure.
"""

from __future__ import annotations

import math
from statistics import mean, pstdev

MAX_MOVE_GAP_MS = 1_000.0   # larger gaps are pauses, not movement segments
MIN_SEGMENT_PX = 1.5        # ignore sub-pixel jitter when measuring direction
TYPING_PAUSE_MIN_MS = 2_000.0
TYPING_PAUSE_MAX_MS = 30_000.0
LATENCY_CAP_MS = 10_000.0


def cv(values: list[float]) -> float | None:
    """cv: (list-of Number) -> Number or None
    Purpose: the coefficient of variation (stddev / mean) of `values`;
    None when it's undefined (fewer than 2 values, or a ~zero mean).
    Examples:
      cv([1.0, 1.0, 1.0]) == 0.0
      cv([5.0]) is None
    """
    if len(values) < 2:
        return None
    m = mean(values)
    if m <= 1e-9:
        return None
    return pstdev(values) / m


def band_score(x: float, a: float, b: float, c: float, d: float) -> float:
    """band_score: Number Number Number Number Number -> Number
    Purpose: trapezoid membership of `x` in the range (a, d), rising from
    0 to 1 across [a, b], flat at 1 across [b, c], falling from 1 to 0
    across [c, d]; 0 at or beyond the outer edges.
    Examples:
      band_score(0, 0, 1, 2, 3) == 0.0
      band_score(1.5, 0, 1, 2, 3) == 1.0
      band_score(4, 0, 1, 2, 3) == 0.0
    """
    if x <= a or x >= d:
        return 0.0
    if b <= x <= c:
        return 1.0
    if x < b:
        return (x - a) / (b - a)
    return (d - x) / (d - c)


def rise_score(x: float, a: float, b: float) -> float:
    """rise_score: Number Number Number -> Number
    Purpose: 0 at or below `a`, 1 at or above `b`, linear in between.
    Examples:
      rise_score(0, 0, 10) == 0.0
      rise_score(10, 0, 10) == 1.0
      rise_score(5, 0, 10) == 0.5
    """
    if x <= a:
        return 0.0
    if x >= b:
        return 1.0
    return (x - a) / (b - a)


def mouse_features(moves: list[tuple[float, float, float]]) -> dict | None:
    """mouse_features: (list-of (t, x, y)) -> dict or None
    Purpose: cursor-velocity/entropy/curvature features over one window of
    (t_ms, x, y) mouse-move samples, sorted by time. None when there
    aren't enough usable segments (fewer than 8 moves, or fewer than 6
    valid speed samples after dropping stale/zero-duration gaps).
    Result keys: n, speed_mean, speed_cv, entropy (0..1, 8-direction-bin
    diversity), curvature (0..1 mean turn angle), reversal_rate (0..1
    fraction of near-180-degree turns) — the latter two are None when no
    segment met MIN_SEGMENT_PX.
    """
    if len(moves) < 8:
        return None
    speeds: list[float] = []
    angles: list[float] = []
    for prev, cur in zip(moves, moves[1:]):
        dt = cur[0] - prev[0]
        if dt <= 0 or dt > MAX_MOVE_GAP_MS:
            continue
        dx, dy = cur[1] - prev[1], cur[2] - prev[2]
        dist = math.hypot(dx, dy)
        speeds.append(dist / dt * 1000.0)
        if dist >= MIN_SEGMENT_PX:
            angles.append(math.atan2(dy, dx))
    if len(speeds) < 6:
        return None

    bins = [0] * 8
    for a in angles:
        bins[int((a + math.pi) / (2 * math.pi) * 8) % 8] += 1
    total = sum(bins)
    entropy = 0.0
    if total:
        for n in bins:
            if n:
                p = n / total
                entropy -= p * math.log2(p)

    turns: list[float] = []
    reversals = 0
    for a1, a2 in zip(angles, angles[1:]):
        diff = abs((a2 - a1 + math.pi) % (2 * math.pi) - math.pi)
        turns.append(diff)
        if diff > 2.6:
            reversals += 1

    return {
        "n": len(speeds),
        "speed_mean": mean(speeds),
        "speed_cv": cv(speeds),
        "entropy": entropy / 3.0,  # 8 direction bins -> max 3 bits
        "curvature": (mean(turns) / math.pi) if turns else None,
        "reversal_rate": (reversals / len(turns)) if turns else None,
    }


def typing_features(key_downs: list[float]) -> dict | None:
    """typing_features: (list-of Number) -> dict or None
    Purpose: inter-key-delay and pause features over one window of sorted
    key-press timestamps (timing only — no key identity). None when fewer
    than 6 key_downs, or fewer than 5 non-pause deltas remain.
    Result keys: n, ikd_mean, ikd_cv (inter-key-delay stats over deltas
    <= TYPING_PAUSE_MIN_MS), pause_count, pause_cv (variability of the
    longer thinking-pause deltas; None below 3 pauses).
    """
    if len(key_downs) < 6:
        return None
    deltas = [b - a for a, b in zip(key_downs, key_downs[1:]) if b > a]
    active = [d for d in deltas if d <= TYPING_PAUSE_MIN_MS]
    pauses = [d for d in deltas if TYPING_PAUSE_MIN_MS < d <= TYPING_PAUSE_MAX_MS]
    if len(active) < 5:
        return None
    return {
        "n": len(active),
        "ikd_mean": mean(active),
        "ikd_cv": cv(active),
        "pause_count": len(pauses),
        "pause_cv": cv(pauses) if len(pauses) >= 3 else None,
    }


def click_features(clicks: list[float]) -> dict | None:
    """click_features: (list-of Number) -> dict or None
    Purpose: click-interval variability over one window of sorted click
    timestamps. None when fewer than 4 clicks or fewer than 3 intervals.
    """
    if len(clicks) < 4:
        return None
    intervals = [b - a for a, b in zip(clicks, clicks[1:]) if b > a]
    if len(intervals) < 3:
        return None
    return {"n": len(intervals), "interval_cv": cv(intervals)}


def scroll_features(scrolls: list[tuple[float, float]]) -> dict | None:
    """scroll_features: (list-of (t, dy)) -> dict or None
    Purpose: scroll-interval variability and direction-change rate over
    one window of sorted (t_ms, dy) samples. None when fewer than 5.
    """
    if len(scrolls) < 5:
        return None
    times = [s[0] for s in scrolls]
    intervals = [b - a for a, b in zip(times, times[1:]) if b > a]
    signs = [1 if s[1] > 0 else -1 for s in scrolls if s[1] != 0]
    changes = sum(1 for a, b in zip(signs, signs[1:]) if a != b)
    return {
        "n": len(scrolls),
        "interval_cv": cv(intervals),
        "direction_change_rate": changes / max(1, len(signs) - 1),
    }


def idle_features(times: list[float], idle_gap_ms: float) -> dict | None:
    """idle_features: (list-of Number) Number -> dict or None
    Purpose: how often the candidate goes idle (a gap > idle_gap_ms
    between consecutive interaction timestamps, for the whole session so
    far) and how variable their recovery pace is afterward. None when
    fewer than 10 timestamps total.
    """
    if len(times) < 10:
        return None
    idle_lengths: list[float] = []
    recovery_gaps: list[float] = []
    for i in range(1, len(times)):
        gap = times[i] - times[i - 1]
        if gap > idle_gap_ms:
            idle_lengths.append(gap)
            if i + 1 < len(times):
                recovery_gaps.append(times[i + 1] - times[i])
    return {
        "idle_count": len(idle_lengths),
        "idle_mean_ms": mean(idle_lengths) if idle_lengths else 0.0,
        "recovery_cv": cv(recovery_gaps) if len(recovery_gaps) >= 2 else None,
    }


def focus_features(
    focus_lost_times: list[float], window_start: float, now: float
) -> dict:
    """focus_features: (list-of Number) Number Number -> dict
    Purpose: how many focus_lost events fell in [window_start, now], and
    the rate per minute of that window. Always returns a result (0 losses
    is itself meaningful, unlike the *_features functions above).
    """
    span_min = max(1e-3, (now - window_start) / 60_000.0)
    losses = [t for t in focus_lost_times if window_start <= t <= now]
    return {"losses": len(losses), "losses_per_min": len(losses) / span_min}


def hidden_ratio(
    visibility_events: list[tuple[float, str]],  # (t, "hidden" | "visible"), sorted
    window_start: float,
    now: float,
) -> float:
    """hidden_ratio: (list-of (t, state)) Number Number -> Number
    Purpose: the fraction of [window_start, now] during which the tab was
    hidden, given a sorted sequence of (t, "hidden"|"visible") transitions.
    Example: with no transitions at all, the tab was visible throughout,
    so hidden_ratio(...) == 0.0.
    """
    state = "visible"
    for t, s in visibility_events:
        if t <= window_start:
            state = s
        else:
            break
    hidden_ms = 0.0
    cursor = window_start
    for t, s in visibility_events:
        if t <= window_start or t > now:
            continue
        if state == "hidden":
            hidden_ms += t - cursor
        cursor = t
        state = s
    if state == "hidden":
        hidden_ms += now - cursor
    span = max(1e-3, now - window_start)
    return min(1.0, hidden_ms / span)


def latency_samples(
    focus_gained_times: list[float], interaction_times: list[float]
) -> list[float]:
    """latency_samples: (list-of Number) (list-of Number) -> (list-of Number)
    Purpose: for each focus_gained timestamp, the time until the next
    interaction (session-wide); samples above LATENCY_CAP_MS are dropped
    as "never really resumed," not counted as extreme latency.
    """
    samples: list[float] = []
    j = 0
    for fg in focus_gained_times:
        while j < len(interaction_times) and interaction_times[j] <= fg:
            j += 1
        if j < len(interaction_times):
            delta = interaction_times[j] - fg
            if delta <= LATENCY_CAP_MS:
                samples.append(delta)
    return samples


def density_features(
    times: list[float], window_start: float, now: float, buckets: int = 10
) -> dict | None:
    """density_features: (list-of Number) Number Number [Number] -> dict or None
    Purpose: interaction-rate and its burst-vs-steady variability across
    [window_start, now], bucketed into `buckets` equal time slices. None
    when fewer than 10 interactions fall in the window.
    """
    in_window = [t for t in times if window_start <= t <= now]
    if len(in_window) < 10:
        return None
    span = max(1e-3, now - window_start)
    counts = [0.0] * buckets
    for t in in_window:
        idx = min(buckets - 1, int((t - window_start) / span * buckets))
        counts[idx] += 1.0
    return {
        "n": len(in_window),
        "events_per_min": len(in_window) / (span / 60_000.0),
        "density_cv": cv(counts),
    }
