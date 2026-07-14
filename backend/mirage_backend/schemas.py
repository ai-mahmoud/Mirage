"""Wire-format data definitions (Pydantic request/response models).

RawEventIn/EventBatch are structurally identical to the ai/ service's
RawEvent/IngestRequest (see ai/mirage_ai/schemas.py) — the backend forwards
them verbatim, so this shape must not drift from that one without updating
both services.
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


class SessionResponse(ApiModel):
    """A SessionResponse describes one InterviewSessionRow as seen by a client."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)

    session_id: str
    candidate_name: str
    interview_type: str
    status: str
    trust_overall: float
    created_at: datetime
    ended_at: Optional[datetime] = None


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
    ai/ service and mirrored into the backend's database for persistence."""

    id: str
    category: str
    title: str
    description: str
    severity: Severity
    polarity: Polarity
    confidence: float
    timestamp: datetime


class RecommendationOut(ApiModel):
    status: str
    label: str
    reasons: list[str]
    suggested_action: str
    human_review_required: bool


class TrustStatusResponse(ApiModel):
    """A TrustStatusResponse is what the Live Session / Dashboard screens
    poll: the current Trust DNA overall score, dual-track confidence, the
    conservative recommendation, and the supporting evidence."""

    session_id: str
    trust_overall: float
    evidence_confidence: float
    recommendation_confidence: float
    current_risk: str
    recommendation: RecommendationOut
    evidence: list[EvidenceOut]
