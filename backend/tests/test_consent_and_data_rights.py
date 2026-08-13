"""Phase 7: consent, retention/purge, export, and right-to-deletion."""

from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from mirage_backend import auth, consent_service, data_rights_service, session_service
from mirage_backend.database import (
    InterviewSessionRow,
    UserConsent,
    make_engine,
    make_session_factory,
    now_utc,
)
from mirage_backend.legal import CURRENT_VERSIONS
from mirage_backend.main import app, get_ai_client, get_db, get_reports_dir
from mirage_backend.schemas import SessionCreate

from .fakes import FakeAiClient

# --- consent_service (direct) ----------------------------------------------


@pytest.fixture
def db():
    engine = make_engine("sqlite:///:memory:")
    factory = make_session_factory(engine)
    session = factory()
    yield session
    session.close()


@pytest.fixture
def user(db):
    return auth.signup(db, "Acme Inc", "ada@acme.com", "password123")


def test_signup_records_every_current_document(db, user):
    status = consent_service.consent_status(db, user.user_id)
    assert status == {doc: True for doc in CURRENT_VERSIONS}


def test_has_current_consent_false_for_unknown_document(db, user):
    assert consent_service.has_current_consent(db, user.user_id, "made_up_document") is False


def test_record_consent_rejects_unknown_document(db, user):
    with pytest.raises(consent_service.UnknownDocument):
        consent_service.record_consent(db, user.user_id, "made_up_document", "2026-01-01")


def test_record_consent_rejects_stale_version(db, user):
    with pytest.raises(consent_service.StaleConsentVersion):
        consent_service.record_consent(db, user.user_id, "privacy_policy", "2020-01-01")


def test_record_consent_accepts_current_version_and_is_recorded(db, user):
    # Clear what signup already recorded, to isolate this call.
    db.query(UserConsent).filter(UserConsent.user_id == user.user_id).delete()
    db.commit()
    assert consent_service.has_current_consent(db, user.user_id, "privacy_policy") is False

    consent_service.record_consent(db, user.user_id, "privacy_policy", CURRENT_VERSIONS["privacy_policy"])
    assert consent_service.has_current_consent(db, user.user_id, "privacy_policy") is True


def test_accepting_the_same_version_twice_is_not_an_error(db, user):
    consent_service.record_consent(
        db, user.user_id, "terms_of_service", CURRENT_VERSIONS["terms_of_service"]
    )
    consent_service.record_consent(
        db, user.user_id, "terms_of_service", CURRENT_VERSIONS["terms_of_service"]
    )
    assert consent_service.has_current_consent(db, user.user_id, "terms_of_service") is True


# --- session_service.purge_expired_sessions --------------------------------


def test_purge_deletes_only_sessions_older_than_retention(db, user):
    ai = FakeAiClient()
    old_ai_id = ai.create_session(
        candidate_name="Old", observer_name="Bob", position=None, department=None, interview_type=None
    )
    old_row = InterviewSessionRow(
        ai_session_id=old_ai_id,
        org_id=user.org_id,
        candidate_name="Old",
        interview_type="Technical Interview",
        created_at=now_utc() - timedelta(days=200),
    )
    db.add(old_row)
    db.commit()

    recent = session_service.create_session(db, ai, SessionCreate(candidate_name="Recent"), user.org_id, user.user_id)

    deleted = session_service.purge_expired_sessions(db, ai, retention_days=90)

    assert deleted == 1
    assert db.get(InterviewSessionRow, old_row.session_id) is None
    assert old_ai_id not in ai._sessions
    assert db.get(InterviewSessionRow, recent.session_id) is not None


def test_purge_is_a_no_op_when_nothing_is_expired(db, user):
    ai = FakeAiClient()
    session_service.create_session(db, ai, SessionCreate(candidate_name="Fresh"), user.org_id, user.user_id)
    assert session_service.purge_expired_sessions(db, ai, retention_days=90) == 0


# --- data_rights_service ----------------------------------------------------


def test_export_includes_org_users_and_sessions(db, user):
    ai = FakeAiClient()
    session_service.create_session(db, ai, SessionCreate(candidate_name="Ada"), user.org_id, user.user_id)

    export = data_rights_service.export_organization_data(db, user.org_id)
    assert export["organization"]["orgId"] == user.org_id
    assert export["users"][0]["email"] == "ada@acme.com"
    assert "hashedPassword" not in export["users"][0] and "hashed_password" not in export["users"][0]
    assert len(export["sessions"]) == 1
    assert export["sessions"][0]["candidateName"] == "Ada"


def test_delete_organization_requires_owner_role(db, user):
    member = auth.signup(db, "Other Org", "member@other.com", "password123")
    member.role = "member"
    member.org_id = user.org_id  # pretend they're a non-owner in user's org
    db.commit()

    with pytest.raises(data_rights_service.NotOrganizationOwner):
        data_rights_service.delete_organization(db, FakeAiClient(), user.org_id, member)


def test_delete_organization_cascades_everything(db, user):
    ai = FakeAiClient()
    row = session_service.create_session(db, ai, SessionCreate(candidate_name="Ada"), user.org_id, user.user_id)
    ai_session_id = row.ai_session_id

    data_rights_service.delete_organization(db, ai, user.org_id, user)

    from mirage_backend.database import InterviewSessionRow, Organization, User

    assert db.get(Organization, user.org_id) is None
    assert db.get(User, user.user_id) is None
    assert db.get(InterviewSessionRow, row.session_id) is None
    assert ai_session_id not in ai._sessions
    assert db.query(UserConsent).filter(UserConsent.user_id == user.user_id).count() == 0


# --- HTTP layer --------------------------------------------------------------


@pytest.fixture
def client(tmp_path):
    engine = make_engine("sqlite:///:memory:")
    factory = make_session_factory(engine)

    def _get_db():
        db = factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[get_ai_client] = lambda: FakeAiClient()
    app.dependency_overrides[get_reports_dir] = lambda: str(tmp_path)
    yield TestClient(app)
    app.dependency_overrides.clear()


def _signup_and_token(client, email="ada@acme.com") -> str:
    resp = client.post("/auth/signup", json={"orgName": "Acme", "email": email, "password": "password123"})
    return resp.json()["accessToken"]


def test_consent_status_over_http_reflects_signup_grants(client):
    token = _signup_and_token(client)
    resp = client.get("/consent/status", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert all(resp.json().values())


def test_post_consent_rejects_stale_version(client):
    token = _signup_and_token(client)
    resp = client.post(
        "/consent",
        json={"document": "privacy_policy", "version": "2000-01-01"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 409


def test_session_creation_returns_428_without_consent(client):
    token = _signup_and_token(client)
    # Simulate an account that predates the consent feature.
    import mirage_backend.main as main_module

    db = next(main_module.app.dependency_overrides[get_db]())
    db.query(UserConsent).delete()
    db.commit()

    resp = client.post(
        "/sessions", json={"candidateName": "Ada"}, headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 428


def test_delete_session_removes_it(client):
    token = _signup_and_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    created = client.post("/sessions", json={"candidateName": "Ada"}, headers=headers)
    session_id = created.json()["sessionId"]

    resp = client.delete(f"/sessions/{session_id}", headers=headers)
    assert resp.status_code == 200

    follow_up = client.get(f"/sessions/{session_id}/trust", headers=headers)
    assert follow_up.status_code == 404


def test_export_endpoint_returns_org_data(client):
    token = _signup_and_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    client.post("/sessions", json={"candidateName": "Ada"}, headers=headers)

    resp = client.get("/users/me/export", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["sessions"]) == 1
    assert body["organization"]["name"] == "Acme"


def test_delete_organization_endpoint_removes_access(client):
    token = _signup_and_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.delete("/organizations/me", headers=headers)
    assert resp.status_code == 200

    # The token is still structurally valid but the user it names is gone.
    follow_up = client.get("/auth/me", headers=headers)
    assert follow_up.status_code == 401
