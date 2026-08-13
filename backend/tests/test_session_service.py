import pytest

from mirage_backend import auth, session_service
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


@pytest.fixture
def org_a(db) -> str:
    # A real Organization row, not a bare string — billing_service.
    # check_session_limit (which create_session calls) needs one to
    # actually exist to read its plan_tier from.
    return auth.signup(db, "Org A", "a@example.com", "password123").org_id


@pytest.fixture
def org_b(db) -> str:
    return auth.signup(db, "Org B", "b@example.com", "password123").org_id


def _payload(**overrides) -> SessionCreate:
    defaults = dict(candidate_name="Ada", interview_type="Technical Interview")
    defaults.update(overrides)
    return SessionCreate(**defaults)


def test_create_session_persists_row_and_registers_with_ai(db, ai, org_a):
    row = session_service.create_session(db, ai, _payload(), org_a)
    assert row.status == "active"
    assert row.trust_overall == 75.0
    assert row.org_id == org_a
    assert row.ai_session_id in ai._sessions


def test_unknown_session_raises_not_found(db, ai, org_a):
    with pytest.raises(session_service.SessionNotFound):
        session_service.current_status(db, ai, "does-not-exist", org_a)


def test_current_status_before_min_events_is_insufficient(db, ai, org_a):
    row = session_service.create_session(db, ai, _payload(), org_a)
    status = session_service.current_status(db, ai, row.session_id, org_a)
    assert status.recommendation.status == "evidence_insufficient"


def test_record_events_mirrors_trust_and_evidence(db, ai, org_a):
    row = session_service.create_session(db, ai, _payload(), org_a)
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
    session_service.record_events(db, ai, row.session_id, events, org_a)

    status = session_service.current_status(db, ai, row.session_id, org_a)
    assert status.trust_overall == 30.0
    assert status.recommendation.status == "manual_review_recommended"
    assert [e.id for e in status.evidence] == ["EV-1"]
    assert status.evidence[0].supporting_signals == ["SIG-008", "SIG-009"]
    assert len(status.trust_dna.dimensions) == 6
    assert status.trust_dna.overall == 30.0


def test_record_events_is_idempotent_on_evidence_id(db, ai, org_a):
    row = session_service.create_session(db, ai, _payload(), org_a)
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

    session_service.record_events(db, ai, row.session_id, [], org_a)
    session_service.record_events(db, ai, row.session_id, [], org_a)  # same card mirrored again

    status = session_service.current_status(db, ai, row.session_id, org_a)
    assert len(status.evidence) == 1


def test_end_session_marks_ended_and_keeps_final_trust(db, ai, org_a):
    row = session_service.create_session(db, ai, _payload(), org_a)
    ended = session_service.end_session(db, ai, row.session_id, org_a)
    assert ended.status == "ended"
    assert ended.ended_at is not None


def test_build_report_caches_executive_summary(db, ai, org_a):
    row = session_service.create_session(db, ai, _payload(), org_a)
    report = session_service.build_report(db, ai, row.session_id, org_a)
    assert report["executiveSummary"] == "Fake summary."
    assert db.get(type(row), row.session_id).executive_summary == "Fake summary."


def test_report_out_returns_structured_report(db, ai, org_a):
    row = session_service.create_session(db, ai, _payload(), org_a)
    report = session_service.report_out(db, ai, row.session_id, org_a)
    assert report.executive_summary == "Fake summary."
    assert len(report.trust_dna.dimensions) == 6
    assert report.privacy_statement


def test_list_sessions_returns_all_most_recent_first(db, ai, org_a):
    first = session_service.create_session(db, ai, _payload(candidate_name="Ada"), org_a)
    second = session_service.create_session(db, ai, _payload(candidate_name="Bo"), org_a)
    rows = session_service.list_sessions(db, org_a)
    assert [r.session_id for r in rows] == [second.session_id, first.session_id]
    assert rows[0].evidence_count == 0


# --- Multi-tenancy isolation ------------------------------------------------


def test_list_sessions_excludes_other_orgs(db, ai, org_a, org_b):
    session_service.create_session(db, ai, _payload(candidate_name="Ada"), org_a)
    session_service.create_session(db, ai, _payload(candidate_name="Bo"), org_b)
    assert [r.candidate_name for r in session_service.list_sessions(db, org_a)] == ["Ada"]
    assert [r.candidate_name for r in session_service.list_sessions(db, org_b)] == ["Bo"]


def test_cross_org_session_access_raises_not_found(db, ai, org_a, org_b):
    row = session_service.create_session(db, ai, _payload(), org_a)
    with pytest.raises(session_service.SessionNotFound):
        session_service.current_status(db, ai, row.session_id, org_b)
    with pytest.raises(session_service.SessionNotFound):
        session_service.record_events(db, ai, row.session_id, [], org_b)
    with pytest.raises(session_service.SessionNotFound):
        session_service.end_session(db, ai, row.session_id, org_b)
    with pytest.raises(session_service.SessionNotFound):
        session_service.report_out(db, ai, row.session_id, org_b)


# --- Plan-limit enforcement (billing_service.PLAN_LIMITS) -----------------


def test_create_session_enforces_the_free_plan_limit(db, ai, org_a):
    from mirage_backend import billing_service

    limit = billing_service.PLAN_LIMITS["free"]
    for _ in range(limit):
        session_service.create_session(db, ai, _payload(), org_a)

    with pytest.raises(billing_service.PlanLimitExceeded):
        session_service.create_session(db, ai, _payload(), org_a)
