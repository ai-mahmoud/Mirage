import pytest
from fastapi.testclient import TestClient

from mirage_backend.database import make_engine, make_session_factory
from mirage_backend.main import app, get_ai_client, get_db, get_reports_dir

from .fakes import FakeAiClient


@pytest.fixture
def client(tmp_path):
    """Unlike test_main_api.py's client fixture, get_current_user is left
    wired to the real dependency here — these tests exercise the actual
    signup/login/token flow, not a faked-authenticated shortcut."""
    engine = make_engine("sqlite:///:memory:")
    factory = make_session_factory(engine)

    def _get_db():
        db = factory()
        try:
            yield db
        finally:
            db.close()

    fake_ai = FakeAiClient()
    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[get_ai_client] = lambda: fake_ai
    app.dependency_overrides[get_reports_dir] = lambda: str(tmp_path)
    yield TestClient(app)
    app.dependency_overrides.clear()


def _signup(client, org_name="Acme", email="ada@acme.com", password="password123"):
    return client.post(
        "/auth/signup", json={"orgName": org_name, "email": email, "password": password}
    )


def test_signup_returns_token_and_user(client):
    resp = _signup(client)
    assert resp.status_code == 200
    body = resp.json()
    assert body["tokenType"] == "bearer"
    assert body["accessToken"]
    assert body["user"]["email"] == "ada@acme.com"
    assert body["user"]["role"] == "owner"


def test_signup_duplicate_email_is_rejected(client):
    _signup(client)
    resp = _signup(client, org_name="Other Org")
    assert resp.status_code == 409


def test_login_with_correct_credentials_succeeds(client):
    _signup(client)
    resp = client.post("/auth/login", json={"email": "ada@acme.com", "password": "password123"})
    assert resp.status_code == 200
    assert resp.json()["user"]["email"] == "ada@acme.com"


def test_login_with_wrong_password_fails(client):
    _signup(client)
    resp = client.post("/auth/login", json={"email": "ada@acme.com", "password": "wrong"})
    assert resp.status_code == 401


def test_login_with_unknown_email_fails(client):
    resp = client.post("/auth/login", json={"email": "nobody@example.com", "password": "x"})
    assert resp.status_code == 401


def test_me_requires_a_bearer_token(client):
    resp = client.get("/auth/me")
    assert resp.status_code == 401


def test_me_returns_the_authenticated_user(client):
    token = _signup(client).json()["accessToken"]
    resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "ada@acme.com"


def test_sessions_route_requires_auth(client):
    resp = client.post("/sessions", json={"candidateName": "Ada"})
    assert resp.status_code == 401


def test_sessions_route_rejects_garbage_token(client):
    resp = client.get("/sessions", headers={"Authorization": "Bearer not-a-real-token"})
    assert resp.status_code == 401


# --- Cross-org isolation, exercised over real HTTP with two real users ----


def test_one_orgs_sessions_are_invisible_to_another(client):
    token_a = _signup(client, org_name="Org A", email="a@example.com").json()["accessToken"]
    token_b = _signup(client, org_name="Org B", email="b@example.com").json()["accessToken"]
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    created = client.post("/sessions", json={"candidateName": "Ada"}, headers=headers_a)
    session_id = created.json()["sessionId"]

    # org B can't see it in their list...
    listed_b = client.get("/sessions", headers=headers_b)
    assert session_id not in [s["sessionId"] for s in listed_b.json()]

    # ...and a direct request for it 404s exactly like it doesn't exist.
    trust_b = client.get(f"/sessions/{session_id}/trust", headers=headers_b)
    assert trust_b.status_code == 404

    # org A can still see their own.
    trust_a = client.get(f"/sessions/{session_id}/trust", headers=headers_a)
    assert trust_a.status_code == 200
