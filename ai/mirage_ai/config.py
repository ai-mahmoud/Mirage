"""Calibrated heuristics for the MVP rule engine.

Every number here is a configurable default, not a scientific constant
(see MVP Bible, "AI Weight Distribution" engineering note). They should
be recalibrated with real validation data after the hackathon.
"""

from dataclasses import dataclass

# Relative contribution of each Trust DNA dimension to the overall score.
TRUST_DNA_WEIGHTS: dict[str, float] = {
    "behavioral_consistency": 0.25,
    "interaction_naturalness": 0.20,
    "attention_stability": 0.20,
    "context_integrity": 0.15,
    "adaptive_responsiveness": 0.10,
    "session_authenticity": 0.10,
}

# Evidential weight of a signal by its reliability grade. Low-grade
# signals (C/D) can support evidence but never dominate it.
RELIABILITY_WEIGHT: dict[str, float] = {
    "A+": 1.0,
    "A": 0.9,
    "B+": 0.75,
    "B": 0.6,
    "C": 0.4,
    "D": 0.2,
}


@dataclass(frozen=True)
class EngineConfig:
    # Sliding analysis windows (milliseconds).
    mouse_window_ms: float = 15_000.0
    typing_window_ms: float = 30_000.0
    focus_window_ms: float = 60_000.0
    # Baseline is frozen from ticks observed in [baseline_start, baseline_end]
    # after session start; later windows are compared against it.
    baseline_start_ms: float = 5_000.0
    baseline_end_ms: float = 35_000.0
    # A per-signal deviation from baseline larger than this counts as a shift.
    shift_threshold: float = 0.35
    # Trust DNA smoothing (exponential moving average).
    ema_alpha: float = 0.35
    # Idle detection.
    idle_gap_ms: float = 5_000.0
    # Evidence lifecycle.
    evidence_cooldown_ms: float = 12_000.0
    positive_evidence_cooldown_ms: float = 30_000.0
    evidence_active_ms: float = 60_000.0
    # Below this event count the session cannot be analyzed at all.
    min_events_for_analysis: int = 25
    # Minimum interval between full pipeline evaluations.
    tick_min_interval_ms: float = 250.0


DEFAULT_CONFIG = EngineConfig()
