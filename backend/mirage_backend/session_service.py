"""Session world-state transitions.

World data definition
----------------------
The "world" is one interview session's persisted state: an
`InterviewSessionRow` (database.py) plus its `EvidenceRow`s. It is created
once by `create_session` and evolves only through the handlers below, each
of which mirrors the ai/ service's authoritative SessionSnapshot onto it:

    create_session : DBSession AiClient SessionCreate -> InterviewSessionRow
    record_events  : world x (list-of RawEventIn) -> world'   (events observed)
    current_status : world -> TrustStatusResponse              (read-only view)
    end_session    : world -> world'                            (session closes)
    build_report   : world -> dict                               (final report)

Every handler takes the SQLAlchemy DBSession and an AiClient explicitly —
no module-level globals — so tests can supply an isolated in-memory
database and a FakeAiClient (tests/fakes.py) instead of a live ai/ process.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session as DBSession

from .ai_client import AiClient
from .database import EvidenceRow, InterviewSessionRow, now_utc
from .schemas import EvidenceOut, RecommendationOut, RawEventIn, SessionCreate, TrustStatusResponse


class SessionNotFound(Exception):
    """Raised when a session_id does not name an existing session."""


def _get_or_raise(db: DBSession, session_id: str) -> InterviewSessionRow:
    """_get_or_raise: DBSession String -> InterviewSessionRow
    Purpose: fetch the session row for `session_id`, or raise SessionNotFound.
    """
    row = db.get(InterviewSessionRow, session_id)
    if row is None:
        raise SessionNotFound(session_id)
    return row


def create_session(db: DBSession, ai: AiClient, payload: SessionCreate) -> InterviewSessionRow:
    """create_session: DBSession AiClient SessionCreate -> InterviewSessionRow
    Purpose: open a new interview session — create its mirrored session in
    the ai/ service first, then persist the local record pointing at it.
    Example:
      create_session(db, fake_ai, SessionCreate(candidate_name="Ada", interview_type="Technical Interview"))
      produces a row with status == "active" and a non-empty ai_session_id.
    """
    ai_session_id = ai.create_session(
        candidate_name=payload.candidate_name,
        observer_name=payload.observer_name or "Interviewer",
        position=payload.position,
        department=payload.department,
        interview_type=payload.interview_type,
    )
    row = InterviewSessionRow(
        ai_session_id=ai_session_id,
        candidate_name=payload.candidate_name,
        interview_type=payload.interview_type,
        position=payload.position,
        department=payload.department,
        observer_name=payload.observer_name,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def _event_to_wire(event: RawEventIn) -> dict:
    """_event_to_wire: RawEventIn -> dict
    Purpose: convert one validated RawEventIn into the plain-dict wire shape
    AiClient.post_events expects, dropping unset optional fields.
    Example:
      _event_to_wire(RawEventIn(type="mouse_click", t=5.0))
      == {"type": "mouse_click", "t": 5.0}
    """
    return event.model_dump(by_alias=True, exclude_none=True)


def record_events(db: DBSession, ai: AiClient, session_id: str, events: list[RawEventIn]) -> dict:
    """record_events: DBSession AiClient String (list-of RawEventIn) -> dict
    Purpose: forward a batch of raw interaction events to the ai/ service,
    then mirror the resulting snapshot (Trust DNA + evidence) into the
    local database. Returns the raw snapshot dict from the ai/ service.
    """
    row = _get_or_raise(db, session_id)
    snapshot = ai.post_events(row.ai_session_id, [_event_to_wire(e) for e in events])
    _apply_snapshot(db, row, snapshot)
    return snapshot


def _apply_snapshot(db: DBSession, row: InterviewSessionRow, snapshot: dict) -> None:
    """_apply_snapshot: DBSession InterviewSessionRow dict -> Void
    Purpose: mirror an ai/ SessionSnapshot dict onto `row`, inserting any
    evidence cards not already persisted. Idempotent on evidence id: mirroring
    the same snapshot twice never duplicates an EvidenceRow.
    """
    row.trust_overall = snapshot["trustDna"]["overall"]
    row.evidence_confidence = snapshot["confidence"]["evidenceConfidence"]
    row.recommendation_confidence = snapshot["confidence"]["recommendationConfidence"]
    row.recommendation_status = snapshot["recommendation"]["status"]
    row.recommendation_label = snapshot["recommendation"]["label"]
    row.current_risk = snapshot["currentRisk"]

    existing_ids = {e.ai_evidence_id for e in row.evidence}
    for card in snapshot["evidence"]:
        if card["id"] in existing_ids:
            continue
        db.add(
            EvidenceRow(
                ai_evidence_id=card["id"],
                session_id=row.session_id,
                category=card["category"],
                title=card["title"],
                description=card["description"],
                severity=card["severity"],
                polarity=card["polarity"],
                confidence=card["confidence"],
                timestamp=datetime.fromtimestamp(card["timestamp"] / 1000.0, tz=timezone.utc),
            )
        )
    db.commit()
    db.refresh(row)


def evidence_row_to_out(row: EvidenceRow) -> EvidenceOut:
    """evidence_row_to_out: EvidenceRow -> EvidenceOut
    Purpose: present a persisted EvidenceRow on the wire.
    """
    return EvidenceOut(
        id=row.ai_evidence_id,
        category=row.category,
        title=row.title,
        description=row.description,
        severity=row.severity,
        polarity=row.polarity,
        confidence=row.confidence,
        timestamp=row.timestamp,
    )


def current_status(db: DBSession, ai: AiClient, session_id: str) -> TrustStatusResponse:
    """current_status: DBSession AiClient String -> TrustStatusResponse
    Purpose: refresh `session_id` from the ai/ service and return its
    current Trust DNA / confidence / recommendation / evidence view.
    """
    row = _get_or_raise(db, session_id)
    snapshot = ai.get_snapshot(row.ai_session_id)
    _apply_snapshot(db, row, snapshot)
    rec = snapshot["recommendation"]
    return TrustStatusResponse(
        session_id=row.session_id,
        trust_overall=row.trust_overall,
        evidence_confidence=row.evidence_confidence,
        recommendation_confidence=row.recommendation_confidence,
        current_risk=row.current_risk,
        recommendation=RecommendationOut(
            status=rec["status"],
            label=rec["label"],
            reasons=rec["reasons"],
            suggested_action=rec["suggestedAction"],
            human_review_required=rec["humanReviewRequired"],
        ),
        evidence=[evidence_row_to_out(e) for e in row.evidence],
    )


def end_session(db: DBSession, ai: AiClient, session_id: str) -> InterviewSessionRow:
    """end_session: DBSession AiClient String -> InterviewSessionRow
    Purpose: pull one final snapshot, mark the session ended, and persist it.
    """
    row = _get_or_raise(db, session_id)
    snapshot = ai.get_snapshot(row.ai_session_id)
    _apply_snapshot(db, row, snapshot)
    row.status = "ended"
    row.ended_at = now_utc()
    db.commit()
    db.refresh(row)
    return row


def build_report(db: DBSession, ai: AiClient, session_id: str) -> dict:
    """build_report: DBSession AiClient String -> dict
    Purpose: fetch the ai/ service's final SessionReport for `session_id`,
    cache its executive summary locally, and return the raw report dict
    (consumed by pdf_service.render_report).
    """
    row = _get_or_raise(db, session_id)
    report = ai.get_report(row.ai_session_id)
    row.executive_summary = report["executiveSummary"]
    db.commit()
    return report
