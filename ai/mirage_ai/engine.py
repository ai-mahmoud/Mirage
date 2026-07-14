"""SessionEngine: the staged evidence-synthesis pipeline (MVP Bible).

    Signal Collection -> Feature Engineering -> Behavior Intelligence Engine
    -> Evidence Reasoning Engine -> Trust DNA Generator
    -> Decision Confidence Engine -> Human Recommendation Layer

Rule-based and deterministic by design: every threshold below is a
calibrated heuristic (see config.py), not a scientific constant, and the
same Signal/EvidenceCard/TrustDna contracts are meant to host a learned
model later without changing the API.
"""

from __future__ import annotations

import itertools
import time

from . import demo
from .config import DEFAULT_CONFIG, RELIABILITY_WEIGHT, TRUST_DNA_WEIGHTS, EngineConfig
from .features import (
    band_score,
    click_features,
    density_features,
    focus_features,
    hidden_ratio,
    idle_features,
    latency_samples,
    mouse_features,
    rise_score,
    scroll_features,
    typing_features,
)
from .schemas import (
    ConfidenceState,
    EventType,
    EvidenceCard,
    Recommendation,
    RawEvent,
    Signal,
    SessionReport,
    SessionSnapshot,
    TimelineEvent,
    TrustDimension,
    TrustDna,
    TrustDnaSample,
)

_ids = itertools.count(1)


def _next_id(prefix: str) -> str:
    return f"{prefix}-{next(_ids):06d}"


# signal_key -> (signal_id, display name, category, reliability grade)
SIGNAL_CATALOGUE: dict[str, tuple[str, str, str, str]] = {
    "cursor_velocity": ("SIG-001", "Cursor Velocity", "mouse", "A"),
    "cursor_entropy": ("SIG-002", "Cursor Entropy", "mouse", "A"),
    "cursor_curvature": ("SIG-003", "Cursor Curvature", "mouse", "B+"),
    "click_rhythm": ("SIG-004", "Click Rhythm", "mouse", "B+"),
    "typing_rhythm": ("SIG-005", "Typing Rhythm", "keyboard", "A"),
    "pause_distribution": ("SIG-006", "Pause Distribution", "keyboard", "B"),
    "idle_recovery": ("SIG-007", "Idle Recovery", "temporal", "B"),
    "window_focus": ("SIG-008", "Window Focus", "attention", "B+"),
    "browser_visibility": ("SIG-009", "Browser Visibility", "attention", "C"),
    "response_latency": ("SIG-010", "Response Latency", "temporal", "B"),
    "interaction_density": ("SIG-011", "Interaction Density", "temporal", "B"),
    "scroll_dynamics": ("SIG-012", "Scroll Dynamics", "mouse", "B"),
    "behavioral_stability": ("SIG-013", "Behavioral Stability", "derived", "A"),
    "attention_drift": ("SIG-014", "Attention Drift", "derived", "B+"),
    "context_continuity": ("SIG-015", "Context Continuity", "derived", "B"),
}

# Which Trust DNA dimension each signal feeds (multiple signals per dimension —
# a dimension never moves on the strength of one signal alone).
DIMENSION_SIGNALS: dict[str, list[str]] = {
    "behavioral_consistency": ["behavioral_stability", "typing_rhythm", "cursor_velocity"],
    "interaction_naturalness": [
        "cursor_velocity",
        "cursor_entropy",
        "cursor_curvature",
        "click_rhythm",
        "scroll_dynamics",
    ],
    "attention_stability": ["window_focus", "browser_visibility", "idle_recovery", "attention_drift"],
    "context_integrity": ["context_continuity", "pause_distribution"],
    "adaptive_responsiveness": ["response_latency", "interaction_density"],
}

# Evidence categories: which signals correlate into a single evidence card.
EVIDENCE_CATEGORIES: dict[str, list[str]] = {
    "interaction_naturalness": [
        "cursor_velocity",
        "cursor_entropy",
        "cursor_curvature",
        "click_rhythm",
        "scroll_dynamics",
    ],
    "attention": ["window_focus", "browser_visibility", "idle_recovery"],
    "consistency": ["response_latency", "interaction_density", "context_continuity", "behavioral_stability"],
}

_CARD_TITLES = {
    "interaction_naturalness": "Mouse interaction pattern shift",
    "attention": "Attention pattern shift",
    "consistency": "Behavioral consistency shift",
}

MIN_SHIFTED_SIGNALS_FOR_EVIDENCE = 2  # multi-signal reasoning: never on one signal alone


def _label(normalized: float) -> str:
    if normalized >= 0.7:
        return "natural"
    if normalized >= 0.4:
        return "borderline"
    return "atypical"


def _window_ts(times: list[float], now: float, span_ms: float) -> list[float]:
    start = now - span_ms
    return [t for t in times if start <= t <= now]


def _window_tuples(seq: list[tuple], now: float, span_ms: float) -> list[tuple]:
    start = now - span_ms
    return [it for it in seq if start <= it[0] <= now]


class SessionEngine:
    """A SessionEngine is one interview session's "world": its raw event
    buffers, its frozen baseline, its Trust DNA scores, and its evidence/
    timeline history. It is created once (analogous to a big-bang initial
    world) and evolves only through its public handlers:

        ingest   : world (list-of RawEvent) -> Void   (buffer new events)
        tick     : world [Number] -> SessionSnapshot   (re-run the pipeline)
        finalize : world [Number] -> SessionReport      (close out the session)

    Everything else on this class is a private helper `tick` calls."""

    def __init__(
        self,
        session_id: str,
        candidate_name: str = "Demo Candidate",
        observer_name: str = "Interviewer",
        position: str | None = None,
        department: str | None = None,
        interview_type: str | None = "Technical Interview",
        demo_mode: bool = False,
        seed: int | None = None,
        config: EngineConfig = DEFAULT_CONFIG,
        started_at: float | None = None,
    ) -> None:
        self.session_id = session_id
        self.candidate_name = candidate_name
        self.observer_name = observer_name
        self.position = position
        self.department = department
        self.interview_type = interview_type
        self.demo_mode = demo_mode
        self.config = config
        self.started_at = started_at if started_at is not None else time.time() * 1000.0
        self.ended_at: float | None = None

        self._moves: list[tuple[float, float, float]] = []
        self._clicks: list[float] = []
        self._scrolls: list[tuple[float, float]] = []
        self._key_downs: list[float] = []
        self._focus_lost: list[float] = []
        self._focus_gained: list[float] = []
        self._visibility: list[tuple[float, str]] = []
        self._all_interaction_times: list[float] = []
        self.total_events = 0

        self._baseline: dict[str, float] | None = None
        self._trust_scores: dict[str, float] = {k: 75.0 for k in TRUST_DNA_WEIGHTS}
        self._last_evidence_at: dict[str, float] = {}
        self._evidence: list[EvidenceCard] = []
        self._timeline: list[TimelineEvent] = []
        self._trust_history: list[TrustDnaSample] = []
        self._last_signals: dict[str, Signal] = {}
        self._last_status: str | None = None
        self._last_tick_ms: float | None = None
        self._last_snapshot: SessionSnapshot | None = None

        self._timeline.append(
            TimelineEvent(t=self.started_at, type="session_started", label="Session started")
        )

        self._demo_events: list[RawEvent] = []
        self._demo_next_idx = 0
        if demo_mode:
            self._demo_events = demo.generate_demo_events(self.started_at, seed=seed)

    # -- ingestion --------------------------------------------------------

    def ingest(self, events: list[RawEvent]) -> None:
        """ingest: (list-of RawEvent) -> Void
        Purpose: file each event into its type's buffer (mutates self),
        bump total_events, and re-sort every buffer by time. Also records
        a TimelineEvent immediately for focus_lost, since that moment
        matters even before the next tick runs the full pipeline.
        """
        for ev in events:
            self.total_events += 1
            t = ev.t
            if ev.type == EventType.mouse_move and ev.x is not None and ev.y is not None:
                self._moves.append((t, ev.x, ev.y))
                self._all_interaction_times.append(t)
            elif ev.type == EventType.mouse_click:
                self._clicks.append(t)
                self._all_interaction_times.append(t)
            elif ev.type == EventType.scroll and ev.dy is not None:
                self._scrolls.append((t, ev.dy))
                self._all_interaction_times.append(t)
            elif ev.type == EventType.key_down:
                self._key_downs.append(t)
                self._all_interaction_times.append(t)
            elif ev.type == EventType.focus_lost:
                self._focus_lost.append(t)
                self._timeline.append(TimelineEvent(t=t, type="focus_lost", label="Window focus lost"))
            elif ev.type == EventType.focus_gained:
                self._focus_gained.append(t)
            elif ev.type == EventType.visibility_hidden:
                self._visibility.append((t, "hidden"))
            elif ev.type == EventType.visibility_visible:
                self._visibility.append((t, "visible"))
        self._moves.sort(key=lambda m: m[0])
        self._clicks.sort()
        self._scrolls.sort(key=lambda s: s[0])
        self._key_downs.sort()
        self._all_interaction_times.sort()

    def _pull_demo_events(self, now: float) -> None:
        """_pull_demo_events: Number -> Void
        Purpose: ingest() every scripted demo event whose timestamp has
        arrived by `now` but hasn't been ingested yet — a no-op unless
        demo_mode is on. This is what makes a demo session self-driving:
        tick() alone reveals the script over time.
        """
        if not self.demo_mode:
            return
        due = []
        while self._demo_next_idx < len(self._demo_events) and self._demo_events[self._demo_next_idx].t <= now:
            due.append(self._demo_events[self._demo_next_idx])
            self._demo_next_idx += 1
        if due:
            self.ingest(due)

    # -- signal extraction --------------------------------------------------

    def _make_signal(
        self, key: str, now: float, value: float, normalized: float, confidence: float, context: str
    ) -> Signal:
        """_make_signal: String Number Number Number Number String -> Signal
        Purpose: look up `key`'s catalogue entry and wrap the computed
        value/normalized/confidence into a Signal, clamping normalized and
        confidence to [0, 1] (feature functions can overshoot slightly).
        """
        signal_id, name, category, reliability = SIGNAL_CATALOGUE[key]
        return Signal(
            signal_id=signal_id,
            name=name,
            category=category,
            timestamp=now,
            value=value,
            normalized_value=max(0.0, min(1.0, normalized)),
            confidence=max(0.0, min(1.0, confidence)),
            reliability=reliability,
            source="behavior_intelligence_engine",
            context=context,
        )

    def _compute_signals(self, now: float) -> dict[str, Signal]:
        """_compute_signals: Number -> (dict String -> Signal)
        Purpose: Feature Engineering + Behavior Intelligence Engine — run
        every features.py function over its window ending at `now`, and
        wrap each usable result into a Signal keyed by signal_key. A key
        absent from the result means that signal wasn't computable this
        tick (missing-data policy: the caller ignores it, not zero-fills).
        """
        cfg = self.config
        signals: dict[str, Signal] = {}

        moves = _window_tuples(self._moves, now, cfg.mouse_window_ms)
        mf = mouse_features(moves)
        if mf:
            if mf["speed_cv"] is not None:
                norm = rise_score(mf["speed_cv"], 0.15, 0.45)
                signals["cursor_velocity"] = self._make_signal(
                    "cursor_velocity",
                    now,
                    mf["speed_cv"],
                    norm,
                    min(1.0, mf["n"] / 40),
                    f"Mouse speed variability is {_label(norm)} (cv={mf['speed_cv']:.2f}, n={mf['n']})",
                )
            norm_e = rise_score(mf["entropy"], 0.15, 0.55)
            signals["cursor_entropy"] = self._make_signal(
                "cursor_entropy",
                now,
                mf["entropy"],
                norm_e,
                min(1.0, mf["n"] / 40),
                f"Movement direction diversity is {_label(norm_e)} (entropy={mf['entropy']:.2f})",
            )
            if mf["reversal_rate"] is not None:
                norm_c = 1.0 - rise_score(mf["reversal_rate"], 0.2, 0.7)
                signals["cursor_curvature"] = self._make_signal(
                    "cursor_curvature",
                    now,
                    mf["reversal_rate"],
                    norm_c,
                    min(1.0, mf["n"] / 40),
                    f"Path curvature is {_label(norm_c)} (reversal rate={mf['reversal_rate']:.2f})",
                )

        clicks = _window_ts(self._clicks, now, cfg.mouse_window_ms)
        cf = click_features(clicks)
        if cf and cf["interval_cv"] is not None:
            norm = rise_score(cf["interval_cv"], 0.15, 0.5)
            signals["click_rhythm"] = self._make_signal(
                "click_rhythm",
                now,
                cf["interval_cv"],
                norm,
                min(1.0, cf["n"] / 10),
                f"Click interval variability is {_label(norm)} (cv={cf['interval_cv']:.2f})",
            )

        scrolls = _window_tuples(self._scrolls, now, cfg.mouse_window_ms)
        sf = scroll_features(scrolls)
        if sf and sf["interval_cv"] is not None:
            norm = rise_score(sf["interval_cv"], 0.15, 0.5)
            signals["scroll_dynamics"] = self._make_signal(
                "scroll_dynamics",
                now,
                sf["interval_cv"],
                norm,
                min(1.0, sf["n"] / 10),
                f"Scroll rhythm is {_label(norm)} (cv={sf['interval_cv']:.2f})",
            )

        key_downs = _window_ts(self._key_downs, now, cfg.typing_window_ms)
        tf = typing_features(key_downs)
        if tf:
            if tf["ikd_cv"] is not None:
                norm = rise_score(tf["ikd_cv"], 0.2, 0.5)
                signals["typing_rhythm"] = self._make_signal(
                    "typing_rhythm",
                    now,
                    tf["ikd_cv"],
                    norm,
                    min(1.0, tf["n"] / 20),
                    f"Inter-key timing variability is {_label(norm)} (cv={tf['ikd_cv']:.2f})",
                )
            if tf["pause_cv"] is not None:
                norm = rise_score(tf["pause_cv"], 0.2, 0.6)
                signals["pause_distribution"] = self._make_signal(
                    "pause_distribution",
                    now,
                    tf["pause_cv"],
                    norm,
                    min(1.0, tf["pause_count"] / 5),
                    f"Pause-length variability is {_label(norm)} (cv={tf['pause_cv']:.2f}, pauses={tf['pause_count']})",
                )

        idf = idle_features(self._all_interaction_times, cfg.idle_gap_ms)
        if idf and idf["recovery_cv"] is not None:
            norm = rise_score(idf["recovery_cv"], 0.15, 0.5)
            signals["idle_recovery"] = self._make_signal(
                "idle_recovery",
                now,
                idf["recovery_cv"],
                norm,
                min(1.0, idf["idle_count"] / 3),
                f"Post-idle recovery pacing is {_label(norm)} (idle events={idf['idle_count']})",
            )

        window_start_focus = max(self.started_at, now - cfg.focus_window_ms)
        ff = focus_features(self._focus_lost, window_start_focus, now)
        span_conf = min(1.0, (now - self.started_at) / cfg.focus_window_ms)
        norm = 1.0 - rise_score(ff["losses_per_min"], 0.5, 4.0)
        signals["window_focus"] = self._make_signal(
            "window_focus",
            now,
            ff["losses_per_min"],
            norm,
            span_conf,
            f"Window-focus stability is {_label(norm)} ({ff['losses']} losses in last window)",
        )

        hr = hidden_ratio(self._visibility, window_start_focus, now)
        norm_v = 1.0 - hr
        signals["browser_visibility"] = self._make_signal(
            "browser_visibility",
            now,
            hr,
            norm_v,
            span_conf,
            f"Tab remained {_label(norm_v)} visible ({hr * 100:.0f}% hidden in last window)",
        )

        samples = latency_samples(
            _window_ts(self._focus_gained, now, cfg.focus_window_ms), self._all_interaction_times
        )
        if samples:
            mean_latency = sum(samples) / len(samples)
            norm = band_score(mean_latency, 80, 300, 2500, 6000)
            signals["response_latency"] = self._make_signal(
                "response_latency",
                now,
                mean_latency,
                norm,
                min(1.0, len(samples) / 3),
                f"Focus-regain response latency is {_label(norm)} ({mean_latency:.0f}ms avg)",
            )

        df = density_features(self._all_interaction_times, window_start_focus, now)
        if df and df["density_cv"] is not None:
            norm = rise_score(df["density_cv"], 0.15, 0.5)
            signals["interaction_density"] = self._make_signal(
                "interaction_density",
                now,
                df["density_cv"],
                norm,
                min(1.0, df["n"] / 30),
                f"Interaction density variability is {_label(norm)} ({df['events_per_min']:.0f} events/min)",
            )

        # -- derived signals: composites over already-computed ones --------
        def _composite(key: str, parts: list[str], label_text: str) -> None:
            vals = [signals[p] for p in parts if p in signals]
            if not vals:
                return
            norm = sum(s.normalized_value for s in vals) / len(vals)
            conf = sum(s.confidence for s in vals) / len(vals)
            signals[key] = self._make_signal(
                key, now, norm, norm, conf, f"{label_text} is {_label(norm)} ({len(vals)} contributing signals)"
            )

        _composite(
            "behavioral_stability",
            ["cursor_velocity", "cursor_entropy", "cursor_curvature", "typing_rhythm"],
            "Overall behavioral stability",
        )
        _composite(
            "attention_drift",
            ["window_focus", "browser_visibility", "idle_recovery"],
            "Attention stability",
        )
        _composite(
            "context_continuity",
            ["response_latency", "interaction_density", "pause_distribution"],
            "Context continuity",
        )

        return signals

    def _establish_baseline(self, signals: dict[str, Signal]) -> None:
        """_establish_baseline: (dict String -> Signal) -> Void
        Purpose: freeze this session's "normal" normalized_value per signal
        key, once, from the config.baseline_start_ms..baseline_end_ms
        window. Every later tick's evidence reasoning measures deviation
        from this snapshot, not from an absolute human-population norm.
        """
        self._baseline = {key: s.normalized_value for key, s in signals.items()}

    # -- evidence reasoning ---------------------------------------------------

    def _reason_evidence(self, now: float, signals: dict[str, Signal]) -> list[EvidenceCard]:
        """_reason_evidence: Number (dict String -> Signal) -> (list-of EvidenceCard)
        Purpose: the Evidence Reasoning Engine. Find signals that deviated
        from baseline by more than cfg.shift_threshold; if two or more
        shifted (MIN_SHIFTED_SIGNALS_FOR_EVIDENCE — never one alone),
        emit one reduces_trust card per affected category, respecting each
        category's cooldown. When nothing shifted and Trust DNA is high,
        occasionally emit a supports_trust card instead. Returns only the
        cards created *this* tick (also appended to self._evidence/timeline).
        """
        cfg = self.config
        new_cards: list[EvidenceCard] = []
        if self._baseline is None:
            return new_cards

        shifted: dict[str, float] = {}
        for key, s in signals.items():
            base = self._baseline.get(key)
            if base is None:
                continue
            deviation = base - s.normalized_value  # positive: got less natural
            if deviation > cfg.shift_threshold:
                shifted[key] = deviation

        if len(shifted) >= MIN_SHIFTED_SIGNALS_FOR_EVIDENCE:
            for category, keys in EVIDENCE_CATEGORIES.items():
                hits = [k for k in keys if k in shifted]
                if not hits:
                    continue
                last_at = self._last_evidence_at.get(category, -1e18)
                if now - last_at < cfg.evidence_cooldown_ms:
                    continue
                severity = "high" if len(hits) >= 3 else "medium" if len(hits) == 2 else "low"
                reliability_w = sum(RELIABILITY_WEIGHT[SIGNAL_CATALOGUE[k][3]] for k in hits) / len(hits)
                conf = sum(signals[k].confidence for k in hits) / len(hits) * reliability_w
                card = EvidenceCard(
                    id=_next_id("EV"),
                    rule=f"{category}_shift",
                    category=category,
                    title=_CARD_TITLES[category],
                    description=(
                        f"{len(hits)} correlated signal(s) moved away from this session's baseline: "
                        + ", ".join(SIGNAL_CATALOGUE[k][1] for k in hits)
                        + "."
                    ),
                    severity=severity,
                    polarity="reduces_trust",
                    confidence=max(0.0, min(1.0, conf)),
                    timestamp=now,
                    supporting_signals=[SIGNAL_CATALOGUE[k][0] for k in hits],
                )
                new_cards.append(card)
                self._last_evidence_at[category] = now

        if not shifted:
            overall = self._weighted_overall()
            last_pos = self._last_evidence_at.get("positive", -1e18)
            if overall >= 80 and now - last_pos >= cfg.positive_evidence_cooldown_ms:
                stable_keys = [k for k in ("behavioral_stability", "cursor_velocity", "typing_rhythm") if k in signals]
                if len(stable_keys) >= MIN_SHIFTED_SIGNALS_FOR_EVIDENCE:
                    card = EvidenceCard(
                        id=_next_id("EV"),
                        rule="sustained_stability",
                        category="consistency",
                        title="Consistent natural interaction sustained",
                        description=(
                            "Multiple independent signals remained within this session's natural baseline range."
                        ),
                        severity="info",
                        polarity="supports_trust",
                        confidence=sum(signals[k].confidence for k in stable_keys) / len(stable_keys),
                        timestamp=now,
                        supporting_signals=[SIGNAL_CATALOGUE[k][0] for k in stable_keys],
                    )
                    new_cards.append(card)
                    self._last_evidence_at["positive"] = now

        for card in new_cards:
            self._evidence.append(card)
            self._timeline.append(
                TimelineEvent(t=now, type="evidence_generated", label=card.title, detail=card.description)
            )
        return new_cards

    # -- trust dna ------------------------------------------------------------

    def _weighted_overall(self) -> float:
        """_weighted_overall: -> Number
        Purpose: the current Trust DNA overall score — self._trust_scores
        combined per config.TRUST_DNA_WEIGHTS.
        """
        return sum(self._trust_scores[k] * w for k, w in TRUST_DNA_WEIGHTS.items())

    def _update_trust_dna(self, signals: dict[str, Signal]) -> TrustDna:
        """_update_trust_dna: (dict String -> Signal) -> TrustDna
        Purpose: the Trust DNA Generator. EMA-smooth each dimension toward
        the mean normalized_value of its mapped signals (DIMENSION_SIGNALS)
        — a dimension with no computable signals this tick simply holds its
        prior value, never resets. session_authenticity is then set as the
        synthesis (mean) of the other five, and trend is derived from the
        per-dimension delta since the previous tick.
        """
        cfg = self.config
        prev_scores = dict(self._trust_scores)

        for dim, keys in DIMENSION_SIGNALS.items():
            vals = [signals[k].normalized_value for k in keys if k in signals]
            if not vals:
                continue
            instant = (sum(vals) / len(vals)) * 100.0
            prev = self._trust_scores[dim]
            self._trust_scores[dim] = cfg.ema_alpha * instant + (1 - cfg.ema_alpha) * prev

        # session_authenticity: synthesis of the other five dimensions.
        others = [v for k, v in self._trust_scores.items() if k != "session_authenticity"]
        self._trust_scores["session_authenticity"] = sum(others) / len(others)

        dims = []
        for key in TRUST_DNA_WEIGHTS:
            score = self._trust_scores[key]
            delta = score - prev_scores[key]
            trend = "up" if delta > 1.0 else "down" if delta < -1.0 else "stable"
            dims.append(
                TrustDimension(
                    id=key,
                    label=key.replace("_", " ").title(),
                    score=round(score, 1),
                    confidence=1.0,
                    trend=trend,
                )
            )
        return TrustDna(dimensions=dims, overall=round(self._weighted_overall(), 1))

    # -- confidence + recommendation ------------------------------------------

    def _decision_confidence(self, signals: dict[str, Signal], evidence: list[EvidenceCard]) -> ConfidenceState:
        """_decision_confidence: (dict String -> Signal) (list-of EvidenceCard) -> ConfidenceState
        Purpose: the Decision Confidence Engine's dual-track output.
        evidence_confidence is the reliability-weighted mean signal
        confidence, scaled down by how many of the 15 defined signals were
        actually computable this tick (missing-data policy). recommendation_
        confidence further discounts that when the most recent evidence
        batch contains conflicting polarities (multi-signal reasoning: a
        contradiction should lower confidence, not force a verdict either way).
        """
        computable = len(signals)
        total_defined = len(SIGNAL_CATALOGUE)
        drivers: list[str] = []

        if not signals:
            drivers.append("No signals computable yet")
            return ConfidenceState(evidence_confidence=0.0, recommendation_confidence=0.0, drivers=drivers)

        weighted_conf = sum(
            s.confidence * RELIABILITY_WEIGHT[SIGNAL_CATALOGUE[k][3]] for k, s in signals.items()
        ) / sum(RELIABILITY_WEIGHT[SIGNAL_CATALOGUE[k][3]] for k in signals)
        coverage = computable / total_defined
        evidence_confidence = weighted_conf * max(0.3, min(1.0, coverage / 0.5))
        drivers.append(f"{computable}/{total_defined} signals available")
        if coverage < 0.5:
            drivers.append("Several signals missing — confidence reduced")

        recent = [e for e in evidence if e.timestamp == evidence[-1].timestamp] if evidence else []
        polarities = {e.polarity for e in recent}
        agreement = 1.0 if len(polarities) <= 1 else 0.5
        if len(polarities) > 1:
            drivers.append("Conflicting evidence signals present")
        recommendation_confidence = evidence_confidence * agreement

        return ConfidenceState(
            evidence_confidence=round(max(0.0, min(1.0, evidence_confidence)), 2),
            recommendation_confidence=round(max(0.0, min(1.0, recommendation_confidence)), 2),
            drivers=drivers,
        )

    def _recommend(
        self, trust_dna: TrustDna, confidence: ConfidenceState, evidence: list[EvidenceCard], computable: int
    ) -> Recommendation:
        """_recommend: TrustDna ConfidenceState (list-of EvidenceCard) Number -> Recommendation
        Purpose: the Human Recommendation Layer — always one of the four
        conservative statuses, ordered most-deferential first:
        evidence_insufficient (not enough data) takes priority over
        manual_review_recommended (low trust, confident, 2+ evidence
        categories — never one category alone), which takes priority over
        additional_observation_recommended (trust or confidence borderline),
        falling through to continue_monitoring. Every branch's `reasons`
        cites specific evidence titles already in self._evidence — the
        recommendation never states a conclusion the evidence list doesn't
        already support.
        """
        cfg = self.config
        recent_negative = [e for e in self._evidence if e.polarity == "reduces_trust"]
        distinct_categories = {e.category for e in recent_negative}

        if self.total_events < cfg.min_events_for_analysis or computable < 3:
            return Recommendation(
                status="evidence_insufficient",
                label="Insufficient Evidence",
                reasons=["Not enough interaction data has been observed yet to form a recommendation"],
                suggested_action="Continue the session to collect more behavioral signals.",
                human_review_required=False,
            )

        if (
            trust_dna.overall < 45
            and confidence.recommendation_confidence >= 0.5
            and len(distinct_categories) >= 2
        ):
            return Recommendation(
                status="manual_review_recommended",
                label="Manual Review Recommended",
                reasons=[e.title for e in recent_negative[-3:]],
                suggested_action="Have the interviewer manually review the flagged evidence before proceeding.",
                human_review_required=True,
            )

        if trust_dna.overall < 65 or confidence.recommendation_confidence < 0.55:
            return Recommendation(
                status="additional_observation_recommended",
                label="Additional Observation Recommended",
                reasons=[e.title for e in recent_negative[-2:]] or ["Behavioral signals are still stabilizing"],
                suggested_action="Continue monitoring for another observation window before deciding.",
                human_review_required=False,
            )

        return Recommendation(
            status="continue_monitoring",
            label="Continue Monitoring",
            reasons=["Behavioral signals remain within this session's natural baseline range"],
            suggested_action="No action needed — continue the interview as normal.",
            human_review_required=False,
        )

    # -- public tick / snapshot ------------------------------------------------

    def tick(self, now: float | None = None) -> SessionSnapshot:
        """tick: [Number] -> SessionSnapshot
        Purpose: run the full pipeline once — pull due demo events, compute
        signals, freeze the baseline once it's due, reason evidence, update
        Trust DNA, compute confidence, recommend — and return the resulting
        SessionSnapshot. Throttled by cfg.tick_min_interval_ms: calling it
        again almost immediately just replays the last snapshot rather than
        recomputing.
        """
        now = now if now is not None else time.time() * 1000.0
        cfg = self.config

        if (
            self._last_tick_ms is not None
            and now - self._last_tick_ms < cfg.tick_min_interval_ms
            and self._last_snapshot is not None
        ):
            return self._last_snapshot

        self._pull_demo_events(now)

        signals = self._compute_signals(now)
        if signals:
            self._last_signals.update(signals)

        if self._baseline is None and now - self.started_at >= cfg.baseline_end_ms:
            baseline_signals = self._compute_signals(
                max(self.started_at + cfg.baseline_start_ms, now - cfg.mouse_window_ms)
            )
            self._establish_baseline(baseline_signals or signals)

        new_evidence = self._reason_evidence(now, signals)
        trust_dna = self._update_trust_dna(signals)
        self._trust_history.append(TrustDnaSample(t=now, overall=trust_dna.overall))
        confidence = self._decision_confidence(signals, self._evidence)
        recommendation = self._recommend(trust_dna, confidence, new_evidence, len(signals))

        if recommendation.status != self._last_status:
            self._timeline.append(
                TimelineEvent(t=now, type="recommendation_updated", label=recommendation.label)
            )
            self._last_status = recommendation.status

        risk_by_status = {
            "evidence_insufficient": "insufficient",
            "continue_monitoring": "low",
            "additional_observation_recommended": "elevated",
            "manual_review_recommended": "review",
        }

        snapshot = SessionSnapshot(
            session_id=self.session_id,
            status="ended" if self.ended_at else "live",
            started_at=self.started_at,
            elapsed_ms=now - self.started_at,
            trust_dna=trust_dna,
            live_signals=list(self._last_signals.values()),
            evidence=list(self._evidence),
            confidence=confidence,
            recommendation=recommendation,
            current_risk=risk_by_status[recommendation.status],
            timeline=list(self._timeline),
        )
        self._last_tick_ms = now
        self._last_snapshot = snapshot
        return snapshot

    def finalize(self, now: float | None = None) -> SessionReport:
        """finalize: [Number] -> SessionReport
        Purpose: run one last tick, mark the session ended, and build the
        immutable SessionReport (executive summary + Trust DNA history +
        the fixed privacy statement) for the Report/Export screen.
        """
        now = now if now is not None else time.time() * 1000.0
        snapshot = self.tick(now)
        self.ended_at = now
        self._timeline.append(TimelineEvent(t=now, type="session_ended", label="Session ended"))

        overall = snapshot.trust_dna.overall
        summary = (
            f"Over {snapshot.elapsed_ms / 60000:.1f} minutes, the session's Trust DNA settled at "
            f"{overall:.0f}/100 across {len(snapshot.evidence)} evidence item(s). "
            f"Current recommendation: {snapshot.recommendation.label}."
        )

        return SessionReport(
            session_id=self.session_id,
            candidate_name=self.candidate_name,
            observer_name=self.observer_name,
            position=self.position,
            department=self.department,
            interview_type=self.interview_type,
            started_at=self.started_at,
            ended_at=self.ended_at,
            duration_ms=self.ended_at - self.started_at,
            generated_at=now,
            executive_summary=summary,
            trust_dna=snapshot.trust_dna,
            trust_dna_history=list(self._trust_history),
            confidence=snapshot.confidence,
            recommendation=snapshot.recommendation,
            evidence=snapshot.evidence,
            timeline=snapshot.timeline,
            privacy_statement=[
                "No keystroke content, clipboard data, audio, or persistent video was collected.",
                "Only interaction metadata was analyzed: cursor movement, timing, focus, and scroll dynamics.",
                "All evidence and recommendations are generated from behavioral metadata only.",
                "A human reviewer makes the final hiring decision — this report is advisory only.",
            ],
        )
