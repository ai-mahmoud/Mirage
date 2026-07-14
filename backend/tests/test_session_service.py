import pytest

from mirage_backend import session_service
from mirage_backend.database import make_engine, make_session_factory
from mirage_backend.schemas import RawEventIn, SessionCreate

from .fakes import FakeAiClient


@pytest.fixture
def db():
    engine = make_engine("sqlite:///:memory:")
    factory = make_session_factory(engine)
    session = factory()
    yield session
    session.close()


@pytest.fixture
def ai():
    return FakeAiClient()


def _payload(**overrides) -> SessionCreate:
    defaults = dict(candidate_name="Ada", interview_type="Technical Interview")
    defaults.update(overrides)
    return SessionCreate(**defaults)


def test_create_session_persists_row_and_registers_with_ai(db, ai):
    row = session_service.create_session(db, ai, _payload())
    assert row.status == "active"
    assert row.trust_overall == 75.0
    assert row.ai_session_id in ai._sessions


def test_unknown_session_raises_not_found(db, ai):
    with pytest.raises(session_service.SessionNotFound):
        session_service.current_status(db, ai, "does-not-exist")


def test_current_status_before_min_events_is_insufficient(db, ai):
    row = session_service.create_session(db, ai, _payload())
    status = session_service.current_status(db, ai, row.session_id)
    assert status.recommendation.status == "evidence_insufficient"


def test_record_events_mirrors_trust_and_evidence(db, ai):
    row = session_service.create_session(db, ai, _payload())
    ai.inject_evidence(
        row.ai_session_id,
        {
            "id": "EV-1",
            "category": "attention",
            "title": "Attention shift",
            "description": "desc",
            "severity": "medium",
            "polarity": "reduces_trust",
            "confidence": 0.7,
            "timestamp": 0.0,
        },
    )
    events = [RawEventIn(type="mouse_move", t=float(i), x=0.0, y=0.0) for i in range(30)]
    session_service.record_events(db, ai, row.session_id, events)

    status = session_service.current_status(db, ai, row.session_id)
    assert status.trust_overall == 30.0
    assert status.recommendation.status == "manual_review_recommended"
    assert [e.id for e in status.evidence] == ["EV-1"]


def test_record_events_is_idempotent_on_evidence_id(db, ai):
    row = session_service.create_session(db, ai, _payload())
    card = {
        "id": "EV-1",
        "category": "attention",
        "title": "t",
        "description": "d",
        "severity": "low",
        "polarity": "reduces_trust",
        "confidence": 0.5,
        "timestamp": 0.0,
    }
    ai.inject_evidence(row.ai_session_id, card)

    session_service.record_events(db, ai, row.session_id, [])
    session_service.record_events(db, ai, row.session_id, [])  # same card mirrored again

    status = session_service.current_status(db, ai, row.session_id)
    assert len(status.evidence) == 1


def test_end_session_marks_ended_and_keeps_final_trust(db, ai):
    row = session_service.create_session(db, ai, _payload())
    ended = session_service.end_session(db, ai, row.session_id)
    assert ended.status == "ended"
    assert ended.ended_at is not None


def test_build_report_caches_executive_summary(db, ai):
    row = session_service.create_session(db, ai, _payload())
    report = session_service.build_report(db, ai, row.session_id)
    assert report["executiveSummary"] == "Fake summary."
    assert db.get(type(row), row.session_id).executive_summary == "Fake summary."
