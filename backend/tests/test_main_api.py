import pytest
from fastapi.testclient import TestClient

from mirage_backend.database import make_engine, make_session_factory
from mirage_backend.main import app, get_ai_client, get_db, get_reports_dir

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

    fake_ai = FakeAiClient()
    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[get_ai_client] = lambda: fake_ai
    app.dependency_overrides[get_reports_dir] = lambda: str(tmp_path)
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_health_check(client):
    assert client.get("/health").json() == {"status": "ok"}


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
