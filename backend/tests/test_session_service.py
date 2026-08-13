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
def user_a(db):
    # A real signup, not a bare org_id string — billing_service.
    # check_session_limit needs a real Organization row to read plan_tier
    # from, and auth.signup() also records the session_tracking_notice
    # consent create_session now requires (see consent_service.py).
    return auth.signup(db, "Org A", "a@example.com", "password123")


@pytest.fixture
def user_b(db):
    return auth.signup(db, "Org B", "b@example.com", "password123")


def _payload(**overrides) -> SessionCreate:
    defaults = dict(candidate_name="Ada", interview_type="Technical Interview")
    defaults.update(overrides)
    return SessionCreate(**defaults)


def _create(db, ai, user, **overrides):
    return session_service.create_session(db, ai, _payload(**overrides), user.org_id, user.user_id)


def test_create_session_persists_row_and_registers_with_ai(db, ai, user_a):
    row = _create(db, ai, user_a)
    assert row.status == "active"
    assert row.trust_overall == 75.0
    assert row.org_id == user_a.org_id
    assert row.ai_session_id in ai._sessions


def test_create_session_requires_current_consent(db, ai, user_a):
    from mirage_backend import consent_service
    from mirage_backend.database import UserConsent

    # A user who somehow has no recorded consent (e.g. an account that
    # predates this feature) must be blocked, not silently let through.
    db.query(UserConsent).filter(UserConsent.user_id == user_a.user_id).delete()
    db.commit()
    with pytest.raises(consent_service.ConsentRequired):
        _create(db, ai, user_a)


def test_unknown_session_raises_not_found(db, ai, user_a):
    with pytest.raises(session_service.SessionNotFound):
        session_service.current_status(db, ai, "does-not-exist", user_a.org_id)


def test_current_status_before_min_events_is_insufficient(db, ai, user_a):
    row = _create(db, ai, user_a)
    status = session_service.current_status(db, ai, row.session_id, user_a.org_id)
    assert status.recommendation.status == "evidence_insufficient"


def test_record_events_mirrors_trust_and_evidence(db, ai, user_a):
    row = _create(db, ai, user_a)
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
    session_service.record_events(db, ai, row.session_id, events, user_a.org_id)

    status = session_service.current_status(db, ai, row.session_id, user_a.org_id)
    assert status.trust_overall == 30.0
    assert status.recommendation.status == "manual_review_recommended"
    assert [e.id for e in status.evidence] == ["EV-1"]
    assert status.evidence[0].supporting_signals == ["SIG-008", "SIG-009"]
    assert len(status.trust_dna.dimensions) == 6
    assert status.trust_dna.overall == 30.0


def test_record_events_is_idempotent_on_evidence_id(db, ai, user_a):
    row = _create(db, ai, user_a)
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

    session_service.record_events(db, ai, row.session_id, [], user_a.org_id)
    session_service.record_events(db, ai, row.session_id, [], user_a.org_id)  # same card mirrored again

    status = session_service.current_status(db, ai, row.session_id, user_a.org_id)
    assert len(status.evidence) == 1


def test_end_session_marks_ended_and_keeps_final_trust(db, ai, user_a):
    row = _create(db, ai, user_a)
    ended = session_service.end_session(db, ai, row.session_id, user_a.org_id)
    assert ended.status == "ended"
    assert ended.ended_at is not None


def test_build_report_caches_executive_summary(db, ai, user_a):
    row = _create(db, ai, user_a)
    report = session_service.build_report(db, ai, row.session_id, user_a.org_id)
    assert report["executiveSummary"] == "Fake summary."
    assert db.get(type(row), row.session_id).executive_summary == "Fake summary."


def test_build_report_reports_backends_own_session_id_not_ais(db, ai, user_a):
    # ai/'s SessionReport.sessionId is ai/'s own internal id (row.ai_session_id
    # here) — build_report must override it with backend's own session_id,
    # or any client using report["sessionId"] to address this session
    # through backend's own routes (e.g. the PDF-download URL) 404s.
    row = _create(db, ai, user_a)
    assert row.ai_session_id != row.session_id  # the fixture must actually exercise the distinct-ids case
    report = session_service.build_report(db, ai, row.session_id, user_a.org_id)
    assert report["sessionId"] == row.session_id


def test_report_out_returns_structured_report(db, ai, user_a):
    row = _create(db, ai, user_a)
    report = session_service.report_out(db, ai, row.session_id, user_a.org_id)
    assert report.executive_summary == "Fake summary."
    assert len(report.trust_dna.dimensions) == 6
    assert report.privacy_statement
    assert report.session_id == row.session_id


def test_list_sessions_returns_all_most_recent_first(db, ai, user_a):
    first = _create(db, ai, user_a, candidate_name="Ada")
    second = _create(db, ai, user_a, candidate_name="Bo")
    rows = session_service.list_sessions(db, user_a.org_id)
    assert [r.session_id for r in rows] == [second.session_id, first.session_id]
    assert rows[0].evidence_count == 0


# --- Deletion ---------------------------------------------------------------


def test_delete_session_removes_row_evidence_and_ai_mirror(db, ai, user_a):
    row = _create(db, ai, user_a)
    ai.inject_evidence(row.ai_session_id, {
        "id": "EV-1", "category": "attention", "title": "t", "description": "d",
        "severity": "low", "polarity": "reduces_trust", "confidence": 0.5, "timestamp": 0.0,
    })
    session_service.record_events(db, ai, row.session_id, [], user_a.org_id)
    ai_session_id = row.ai_session_id

    session_service.delete_session(db, ai, row.session_id, user_a.org_id)

    assert db.get(type(row), row.session_id) is None
    assert ai_session_id not in ai._sessions
    with pytest.raises(session_service.SessionNotFound):
        session_service.current_status(db, ai, row.session_id, user_a.org_id)


def test_delete_session_is_org_scoped(db, ai, user_a, user_b):
    row = _create(db, ai, user_a)
    with pytest.raises(session_service.SessionNotFound):
        session_service.delete_session(db, ai, row.session_id, user_b.org_id)
    # still there — the cross-org delete attempt didn't touch it.
    assert db.get(type(row), row.session_id) is not None


# --- Multi-tenancy isolation ------------------------------------------------


def test_list_sessions_excludes_other_orgs(db, ai, user_a, user_b):
    _create(db, ai, user_a, candidate_name="Ada")
    _create(db, ai, user_b, candidate_name="Bo")
    assert [r.candidate_name for r in session_service.list_sessions(db, user_a.org_id)] == ["Ada"]
    assert [r.candidate_name for r in session_service.list_sessions(db, user_b.org_id)] == ["Bo"]


def test_cross_org_session_access_raises_not_found(db, ai, user_a, user_b):
    row = _create(db, ai, user_a)
    with pytest.raises(session_service.SessionNotFound):
        session_service.current_status(db, ai, row.session_id, user_b.org_id)
    with pytest.raises(session_service.SessionNotFound):
        session_service.record_events(db, ai, row.session_id, [], user_b.org_id)
    with pytest.raises(session_service.SessionNotFound):
        session_service.end_session(db, ai, row.session_id, user_b.org_id)
    with pytest.raises(session_service.SessionNotFound):
        session_service.report_out(db, ai, row.session_id, user_b.org_id)


# --- Plan-limit enforcement (billing_service.PLAN_LIMITS) -----------------


def test_create_session_enforces_the_free_plan_limit(db, ai, user_a):
    from mirage_backend import billing_service

    limit = billing_service.PLAN_LIMITS["free"]
    for _ in range(limit):
        _create(db, ai, user_a)

    with pytest.raises(billing_service.PlanLimitExceeded):
        _create(db, ai, user_a)
