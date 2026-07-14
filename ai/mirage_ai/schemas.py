"""Pydantic models shared by the engine and the API.

All API payloads use camelCase aliases (JS-friendly). RawEvent forbids
extra fields, so the service is physically unable to accept keystroke
content, clipboard data, or any payload beyond timestamps/coordinates.

Every class below is a How-to-Design-Data data definition: the docstring
states what the type represents and, where it isn't obvious from the
field names, what each field means.
"""

from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class ApiModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class EventType(str, Enum):
    """An EventType is one of the nine interaction-metadata kinds the
    client's tracking engine may report. There is deliberately no event
    type for keystroke identity, clipboard, audio, or video."""

    mouse_move = "mouse_move"
    mouse_click = "mouse_click"
    scroll = "scroll"
    key_down = "key_down"  # timing only — no key identity exists in the schema
    key_up = "key_up"
    focus_gained = "focus_gained"
    focus_lost = "focus_lost"
    visibility_visible = "visibility_visible"
    visibility_hidden = "visibility_hidden"


class RawEvent(ApiModel):
    """A RawEvent is one client-timestamped interaction sample:
        type - an EventType
        t    - epoch milliseconds (Date.now() on the client)
        x, y - cursor position, present for mouse_move only
        dy   - scroll delta, present for scroll only
    extra="forbid" means any field beyond these four is a validation
    error, not a silently-accepted payload — this is what makes "no
    keystroke content ever reaches this service" an enforced property
    rather than a convention.
    """

    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, extra="forbid"
    )

    type: EventType
    t: float
    x: Optional[float] = None
    y: Optional[float] = None
    dy: Optional[float] = None


class Signal(ApiModel):
    """A Signal is one behavioral-intelligence reading, per the MVP Bible's
    unified signal metadata schema:
        signal_id        - "SIG-001".."SIG-015"
        value             - the raw feature value (units vary by signal)
        normalized_value  - 0..1 "naturalness" score derived from `value`
        confidence        - 0..1, driven by sample size / data quality
        reliability       - grade "A+".."D"; low grades must never
                             independently drive a recommendation
        context           - human-readable interpretation (explainability)
    """

    signal_id: str
    name: str
    category: str
    timestamp: float
    value: float
    normalized_value: float
    confidence: float
    reliability: str
    source: str
    context: str


Severity = Literal["info", "low", "medium", "high"]
Polarity = Literal["supports_trust", "reduces_trust", "informational"]


class EvidenceCard(ApiModel):
    """An EvidenceCard is one human-readable piece of evidence, synthesized
    by correlating two or more Signals (see engine.py,
    MIN_SHIFTED_SIGNALS_FOR_EVIDENCE) — never generated from a single
    signal alone. `polarity` records whether it raises or lowers trust;
    `supporting_signals` names the Signal ids (not full Signals) behind it."""

    id: str
    rule: str
    category: str
    title: str
    description: str
    severity: Severity
    polarity: Polarity
    confidence: float
    timestamp: float
    supporting_signals: list[str]


class TrustDimension(ApiModel):
    """A TrustDimension is one of the six independently-evolving facets of
    Trust DNA (see config.TRUST_DNA_WEIGHTS): a 0..100 score, how it
    changed since the previous tick (`trend`), and a confidence value."""

    id: str
    label: str
    score: float
    confidence: float
    trend: Literal["up", "down", "stable"]


class TrustDna(ApiModel):
    """A TrustDna is the full replacement for a single trust score: all six
    TrustDimensions plus their weighted synthesis (`overall`, 0..100)."""

    dimensions: list[TrustDimension]
    overall: float


RecommendationStatus = Literal[
    "continue_monitoring",
    "evidence_insufficient",
    "additional_observation_recommended",
    "manual_review_recommended",
]


class Recommendation(ApiModel):
    """A Recommendation is the Human Recommendation Layer's output: always
    one of the four conservative RecommendationStatus values above — never
    "reject" or "cheating detected" — with `reasons` citing the evidence
    that produced it (evidence always precedes the conclusion)."""

    status: RecommendationStatus
    label: str
    reasons: list[str]
    suggested_action: str
    human_review_required: bool


class ConfidenceState(ApiModel):
    """A ConfidenceState is the Decision Confidence Engine's dual-track
    output: evidence_confidence (how much data backs the evidence itself)
    and recommendation_confidence (how much that evidence agrees) are
    always computed and shown separately, never collapsed into one number."""

    evidence_confidence: float
    recommendation_confidence: float
    drivers: list[str]


class TimelineEvent(ApiModel):
    """A TimelineEvent is one notable moment in a session's history:
    type is one of session_started | focus_lost | evidence_generated |
    recommendation_updated | session_ended."""

    t: float
    type: str
    label: str
    detail: Optional[str] = None


class TrustDnaSample(ApiModel):
    """A TrustDnaSample is one (time, overall Trust DNA score) point,
    collected once per tick to build the Session Report's history chart."""

    t: float
    overall: float


class SessionSnapshot(ApiModel):
    """A SessionSnapshot is the complete state of one live session at a
    single tick — everything the Live Session screen needs to render:
    Trust DNA, the signals currently computable, all evidence generated
    so far, dual confidence, the current recommendation, a risk-level
    summary of that recommendation, and the session's timeline."""

    session_id: str
    status: Literal["live", "ended"]
    started_at: float
    elapsed_ms: float
    trust_dna: TrustDna
    live_signals: list[Signal]
    evidence: list[EvidenceCard]
    confidence: ConfidenceState
    recommendation: Recommendation
    current_risk: Literal["low", "elevated", "review", "insufficient"]
    timeline: list[TimelineEvent]


class SessionReport(ApiModel):
    """A SessionReport is the final, immutable summary of an ended session
    — the Session Report / Export screen's data source. Distinct from
    SessionSnapshot in carrying an executive summary, the full Trust DNA
    history, and a fixed privacy statement, rather than a single instant."""

    session_id: str
    candidate_name: str
    observer_name: str
    position: Optional[str]
    department: Optional[str]
    interview_type: Optional[str]
    started_at: float
    ended_at: float
    duration_ms: float
    generated_at: float
    executive_summary: str
    trust_dna: TrustDna
    trust_dna_history: list[TrustDnaSample]
    confidence: ConfidenceState
    recommendation: Recommendation
    evidence: list[EvidenceCard]
    timeline: list[TimelineEvent]
    privacy_statement: list[str]


class CreateSessionRequest(ApiModel):
    """A CreateSessionRequest starts a new session. `demo=True` makes the
    engine self-drive a scripted dataset (see demo.py) instead of waiting
    for real events — the offline fallback if live tracking is unstable."""

    candidate_name: str = "Demo Candidate"
    observer_name: str = "Interviewer"
    position: Optional[str] = None
    department: Optional[str] = None
    interview_type: Optional[str] = "Technical Interview"
    demo: bool = False
    seed: Optional[int] = None


class CreateSessionResponse(ApiModel):
    session_id: str
    started_at: float
    demo: bool


class IngestRequest(ApiModel):
    """An IngestRequest is one batch of RawEvents posted to
    POST /sessions/{id}/events."""

    events: list[RawEvent] = Field(default_factory=list)
