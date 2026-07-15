"""Wire-format data definitions (Pydantic request/response models).

RawEventIn/EventBatch are structurally identical to the ai/ service's
RawEvent/IngestRequest (see ai/mirage_ai/schemas.py) — the backend forwards
them verbatim, so this shape must not drift from that one without updating
both services. TrustDimensionOut/TrustDnaOut/ConfidenceOut/TimelineEventOut/
TrustDnaSampleOut/SessionReportOut similarly mirror ai/'s own schemas.py
field-for-field (same camelCase aliases), so a raw ai/ response dict can be
parsed straight into them with `Model.model_validate(...)` — no manual
field-by-field mapping.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class ApiModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


# --- Session -----------------------------------------------------------


class SessionCreate(ApiModel):
    """A SessionCreate is the payload a client sends to start an interview
    session: who is being interviewed, by whom, and for what role."""

    candidate_name: str
    interview_type: str = "Technical Interview"
    position: Optional[str] = None
    department: Optional[str] = None
    observer_name: Optional[str] = None


class TrustDimensionOut(ApiModel):
    id: str
    label: str
    score: float
    trend: Literal["up", "down", "stable"]


class TrustDnaOut(ApiModel):
    dimensions: list[TrustDimensionOut]
    overall: float


class SessionResponse(ApiModel):
    """A SessionResponse describes one InterviewSessionRow as seen by a
    client — identity, lifecycle, and its latest mirrored ai/ state
    (everything a Dashboard sessions-list row or a detail page needs,
    without a further round-trip)."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)

    session_id: str
    candidate_name: str
    interview_type: str
    position: Optional[str] = None
    department: Optional[str] = None
    observer_name: Optional[str] = None

    status: str
    created_at: datetime
    ended_at: Optional[datetime] = None

    trust_overall: float
    trust_dimensions: list[TrustDimensionOut] = Field(default_factory=list)
    evidence_confidence: float
    recommendation_confidence: float
    recommendation_status: str
    recommendation_label: str
    evidence_count: int


# --- Raw behavioral events (forwarded verbatim to the ai/ service) -----


class EventType(str, Enum):
    mouse_move = "mouse_move"
    mouse_click = "mouse_click"
    scroll = "scroll"
    key_down = "key_down"
    key_up = "key_up"
    focus_gained = "focus_gained"
    focus_lost = "focus_lost"
    visibility_visible = "visibility_visible"
    visibility_hidden = "visibility_hidden"


class RawEventIn(ApiModel):
    """A RawEventIn is one interaction-metadata sample from the client's
    tracking engine: an event type, a client timestamp (epoch-ms), and,
    for mouse/scroll events, coordinates. Never carries keystroke content
    — extra="forbid" makes any such field a validation error, not a
    silent pass-through."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="forbid")

    type: EventType
    t: float
    x: Optional[float] = None
    y: Optional[float] = None
    dy: Optional[float] = None


class EventBatch(ApiModel):
    events: list[RawEventIn] = Field(default_factory=list)


# --- Evidence + recommendation (mirrored from the ai/ service) --------

Severity = Literal["info", "low", "medium", "high"]
Polarity = Literal["supports_trust", "reduces_trust", "informational"]


class EvidenceOut(ApiModel):
    """An EvidenceOut is one human-readable evidence card, sourced from the
    ai/ service and mirrored into the backend's database for persistence.
    `supporting_signals` (signal ids) is what makes it explainable rather
    than an assertion — every card names the signals behind it."""

    id: str
    category: str
    title: str
    description: str
    severity: Severity
    polarity: Polarity
    confidence: float
    timestamp: datetime
    supporting_signals: list[str] = Field(default_factory=list)


class RecommendationOut(ApiModel):
    status: str
    label: str
    reasons: list[str]
    suggested_action: str
    human_review_required: bool


class TrustStatusResponse(ApiModel):
    """A TrustStatusResponse is what the Live Session screen (and the
    bonus detail pages) poll: the full Trust DNA (all 6 dimensions, not
    just the overall score), dual-track confidence, the conservative
    recommendation, and the supporting evidence."""

    session_id: str
    trust_overall: float
    trust_dna: TrustDnaOut
    evidence_confidence: float
    recommendation_confidence: float
    current_risk: str
    recommendation: RecommendationOut
    evidence: list[EvidenceOut]


# --- Session report (JSON, for the Report screen; PDF is a separate export) --


class ConfidenceOut(ApiModel):
    evidence_confidence: float
    recommendation_confidence: float
    drivers: list[str]


class TimelineEventOut(ApiModel):
    t: float
    type: str
    label: str
    detail: Optional[str] = None


class TrustDnaSampleOut(ApiModel):
    t: float
    overall: float


class SessionReportOut(ApiModel):
    """A SessionReportOut is the final, structured report for the Report
    screen — mirrors ai/'s SessionReport exactly. PDF export
    (GET /sessions/{id}/report/pdf) is rendered from the same data, kept
    separate from this JSON view per the product's screen/export split."""

    session_id: str
    candidate_name: str
    observer_name: str
    position: Optional[str] = None
    department: Optional[str] = None
    interview_type: Optional[str] = None
    started_at: float
    ended_at: float
    duration_ms: float
    generated_at: float
    executive_summary: str
    trust_dna: TrustDnaOut
    trust_dna_history: list[TrustDnaSampleOut]
    confidence: ConfidenceOut
    recommendation: RecommendationOut
    evidence: list[EvidenceOut]
    timeline: list[TimelineEventOut]
    privacy_statement: list[str]
