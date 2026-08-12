import pytest
from fastapi.testclient import TestClient

from mirage_backend import auth
from mirage_backend.database import make_engine, make_session_factory
from mirage_backend.main import app, get_ai_client, get_current_user, get_db, get_reports_dir

from .fakes import FakeAiClient


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

    # Most tests here exercise the session routes' own logic, not auth
    # itself (that's test_auth.py's job) — so a fixed, always-authenticated
    # fake user is the default override, same spirit as FakeAiClient.
    db_for_setup = factory()
    fake_user = auth.signup(db_for_setup, "Test Org", "test@example.com", "password123")
    db_for_setup.close()

    fake_ai = FakeAiClient()
    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[get_ai_client] = lambda: fake_ai
    app.dependency_overrides[get_reports_dir] = lambda: str(tmp_path)
    app.dependency_overrides[get_current_user] = lambda: fake_user
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_health_check(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "database": "connected"}


def test_full_session_lifecycle(client):
    created = client.post("/sessions", json={"candidateName": "Ada", "interviewType": "Technical Interview"})
    assert created.status_code == 200
    session_id = created.json()["sessionId"]

    events_resp = client.post(
        f"/sessions/{session_id}/events",
        json={"events": [{"type": "mouse_move", "t": 1.0, "x": 1.0, "y": 2.0}]},
    )
    assert events_resp.status_code == 200
    assert events_resp.json()["recommendation"]["status"] == "evidence_insufficient"

    trust_resp = client.get(f"/sessions/{session_id}/trust")
    assert trust_resp.status_code == 200

    report_resp = client.get(f"/sessions/{session_id}/report")
    assert report_resp.status_code == 200
    assert report_resp.json()["executiveSummary"] == "Fake summary."

    pdf_resp = client.get(f"/sessions/{session_id}/report/pdf")
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"

    end_resp = client.post(f"/sessions/{session_id}/end")
    assert end_resp.status_code == 200
    assert end_resp.json()["status"] == "ended"


def test_list_sessions_includes_created_session(client):
    created = client.post("/sessions", json={"candidateName": "Ada", "interviewType": "Technical Interview"})
    session_id = created.json()["sessionId"]

    listed = client.get("/sessions")
    assert listed.status_code == 200
    ids = [s["sessionId"] for s in listed.json()]
    assert session_id in ids


def test_unknown_session_returns_404(client):
    resp = client.get("/sessions/does-not-exist/trust")
    assert resp.status_code == 404


def test_every_response_carries_a_request_id_header(client):
    resp = client.get("/health")
    assert resp.headers.get("x-request-id")


# --- Observability: health degradation + the generic 500 handler --------


def test_health_check_returns_503_when_database_unreachable(client):
    class BrokenDb:
        def execute(self, *args, **kwargs):
            raise RuntimeError("connection refused")

    app.dependency_overrides[get_db] = lambda: BrokenDb()
    resp = client.get("/health")
    assert resp.status_code == 503
    assert resp.json() == {"status": "degraded", "database": "unreachable"}


def test_unhandled_exception_returns_generic_500_with_request_id(client):
    class ExplodingAiClient:
        def create_session(self, **kwargs):
            raise RuntimeError("boom — not a known failure mode")

    app.dependency_overrides[get_ai_client] = lambda: ExplodingAiClient()
    # TestClient's default raise_server_exceptions=True re-raises even an
    # exception a registered handler already converted to a response
    # (deliberate Starlette/FastAPI behavior, so a real bug isn't silently
    # swallowed in tests) — disabled here since observing the handler's
    # actual response IS the point of this test.
    no_raise_client = TestClient(app, raise_server_exceptions=False)
    resp = no_raise_client.post("/sessions", json={"candidateName": "Ada"})
    assert resp.status_code == 500
    body = resp.json()
    assert body["detail"] == "Internal server error"
    assert body["requestId"]
    # ...and it's the same id the response header carries, for correlation.
    assert body["requestId"] == resp.headers["x-request-id"]
