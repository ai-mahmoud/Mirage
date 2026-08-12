import pytest

from mirage_backend import session_service
from mirage_backend.database import make_engine, make_session_factory
from mirage_backend.schemas import RawEventIn, SessionCreate

from .fakes import FakeAiClient

ORG_A = "org-a"
ORG_B = "org-b"


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
    row = session_service.create_session(db, ai, _payload(), ORG_A)
    assert row.status == "active"
    assert row.trust_overall == 75.0
    assert row.org_id == ORG_A
    assert row.ai_session_id in ai._sessions


def test_unknown_session_raises_not_found(db, ai):
    with pytest.raises(session_service.SessionNotFound):
        session_service.current_status(db, ai, "does-not-exist", ORG_A)


def test_current_status_before_min_events_is_insufficient(db, ai):
    row = session_service.create_session(db, ai, _payload(), ORG_A)
    status = session_service.current_status(db, ai, row.session_id, ORG_A)
    assert status.recommendation.status == "evidence_insufficient"


def test_record_events_mirrors_trust_and_evidence(db, ai):
    row = session_service.create_session(db, ai, _payload(), ORG_A)
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
            "supportingSignals": ["SIG-008", "SIG-009"],
        },
    )
    events = [RawEventIn(type="mouse_move", t=float(i), x=0.0, y=0.0) for i in range(30)]
    session_service.record_events(db, ai, row.session_id, events, ORG_A)

    status = session_service.current_status(db, ai, row.session_id, ORG_A)
    assert status.trust_overall == 30.0
    assert status.recommendation.status == "manual_review_recommended"
    assert [e.id for e in status.evidence] == ["EV-1"]
    assert status.evidence[0].supporting_signals == ["SIG-008", "SIG-009"]
    assert len(status.trust_dna.dimensions) == 6
    assert status.trust_dna.overall == 30.0


def test_record_events_is_idempotent_on_evidence_id(db, ai):
    row = session_service.create_session(db, ai, _payload(), ORG_A)
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

    session_service.record_events(db, ai, row.session_id, [], ORG_A)
    session_service.record_events(db, ai, row.session_id, [], ORG_A)  # same card mirrored again

    status = session_service.current_status(db, ai, row.session_id, ORG_A)
    assert len(status.evidence) == 1


def test_end_session_marks_ended_and_keeps_final_trust(db, ai):
    row = session_service.create_session(db, ai, _payload(), ORG_A)
    ended = session_service.end_session(db, ai, row.session_id, ORG_A)
    assert ended.status == "ended"
    assert ended.ended_at is not None


def test_build_report_caches_executive_summary(db, ai):
    row = session_service.create_session(db, ai, _payload(), ORG_A)
    report = session_service.build_report(db, ai, row.session_id, ORG_A)
    assert report["executiveSummary"] == "Fake summary."
    assert db.get(type(row), row.session_id).executive_summary == "Fake summary."


def test_report_out_returns_structured_report(db, ai):
    row = session_service.create_session(db, ai, _payload(), ORG_A)
    report = session_service.report_out(db, ai, row.session_id, ORG_A)
    assert report.executive_summary == "Fake summary."
    assert len(report.trust_dna.dimensions) == 6
    assert report.privacy_statement


def test_list_sessions_returns_all_most_recent_first(db, ai):
    first = session_service.create_session(db, ai, _payload(candidate_name="Ada"), ORG_A)
    second = session_service.create_session(db, ai, _payload(candidate_name="Bo"), ORG_A)
    rows = session_service.list_sessions(db, ORG_A)
    assert [r.session_id for r in rows] == [second.session_id, first.session_id]
    assert rows[0].evidence_count == 0


# --- Multi-tenancy isolation ------------------------------------------------


def test_list_sessions_excludes_other_orgs(db, ai):
    session_service.create_session(db, ai, _payload(candidate_name="Ada"), ORG_A)
    session_service.create_session(db, ai, _payload(candidate_name="Bo"), ORG_B)
    assert [r.candidate_name for r in session_service.list_sessions(db, ORG_A)] == ["Ada"]
    assert [r.candidate_name for r in session_service.list_sessions(db, ORG_B)] == ["Bo"]


def test_cross_org_session_access_raises_not_found(db, ai):
    row = session_service.create_session(db, ai, _payload(), ORG_A)
    with pytest.raises(session_service.SessionNotFound):
        session_service.current_status(db, ai, row.session_id, ORG_B)
    with pytest.raises(session_service.SessionNotFound):
        session_service.record_events(db, ai, row.session_id, [], ORG_B)
    with pytest.raises(session_service.SessionNotFound):
        session_service.end_session(db, ai, row.session_id, ORG_B)
    with pytest.raises(session_service.SessionNotFound):
        session_service.report_out(db, ai, row.session_id, ORG_B)
