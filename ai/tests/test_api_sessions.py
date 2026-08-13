"""API-layer coverage for the session CRUD routes (create/ingest/get/
report/delete/seed-list) and CORS — the gap flagged back when
test_api.py was first added (Phase 4: "Session-route coverage is Phase
5's job") and never actually filled in. test_api.py stays narrowly
about observability; this file is the session-routes counterpart.
"""

import pytest
from fastapi.testclient import TestClient

from mirage_ai.api import app, get_store
from mirage_ai.store import InMemorySessionStore


@pytest.fixture
def client():
    store = InMemorySessionStore()
    app.dependency_overrides[get_store] = lambda: store
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_create_session_returns_id_and_started_at(client):
    resp = client.post("/sessions", json={"candidateName": "Ada", "interviewType": "Technical Interview"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["sessionId"]
    assert body["startedAt"] > 0
    assert body["demo"] is False


def test_create_session_defaults_when_fields_omitted(client):
    resp = client.post("/sessions", json={})
    assert resp.status_code == 200
    assert resp.json()["sessionId"]


def test_get_unknown_session_returns_404(client):
    for path in ["/sessions/nope", "/sessions/nope/report"]:
        assert client.get(path).status_code == 404
    assert client.delete("/sessions/nope").status_code == 404
    assert client.post("/sessions/nope/events", json={"events": []}).status_code == 404


def test_ingest_events_accumulates_and_snapshot_reflects_them(client):
    session_id = client.post("/sessions", json={"candidateName": "Ada"}).json()["sessionId"]

    events = [
        {"type": "mouse_move", "t": float(i * 50), "x": float(i), "y": float(i)} for i in range(40)
    ]
    resp = client.post(f"/sessions/{session_id}/events", json={"events": events})
    assert resp.status_code == 200
    snapshot = resp.json()
    assert snapshot["sessionId"] == session_id
    assert snapshot["status"] == "live"

    follow_up = client.get(f"/sessions/{session_id}")
    assert follow_up.status_code == 200
    assert follow_up.json()["status"] == "live"


def test_below_min_events_recommendation_is_insufficient(client):
    session_id = client.post("/sessions", json={"candidateName": "Ada"}).json()["sessionId"]
    resp = client.get(f"/sessions/{session_id}")
    assert resp.json()["recommendation"]["status"] == "evidence_insufficient"


def test_report_finalizes_the_session(client):
    session_id = client.post("/sessions", json={"candidateName": "Ada"}).json()["sessionId"]
    resp = client.get(f"/sessions/{session_id}/report")
    assert resp.status_code == 200
    report = resp.json()
    assert report["sessionId"] == session_id
    assert report["endedAt"] > 0
    assert report["privacyStatement"]

    # A live session's own GET now reflects "ended" — finalize() closes it.
    follow_up = client.get(f"/sessions/{session_id}")
    assert follow_up.json()["status"] == "ended"


def test_delete_session_then_404(client):
    session_id = client.post("/sessions", json={"candidateName": "Ada"}).json()["sessionId"]
    resp = client.delete(f"/sessions/{session_id}")
    assert resp.status_code == 200
    assert resp.json() == {"status": "deleted", "session_id": session_id}
    assert client.get(f"/sessions/{session_id}").status_code == 404


def test_demo_mode_self_drives_without_real_events(client):
    session_id = client.post("/sessions", json={"candidateName": "Ada", "demo": True, "seed": 7}).json()["sessionId"]
    # A demo session generates its own scripted events over time — even a
    # bare GET (which ticks the pipeline forward) should eventually surface
    # signals without the caller ever posting a single real event.
    resp = client.get(f"/sessions/{session_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "live"


def test_seed_sessions_lists_only_what_the_store_actually_has(client):
    empty = client.get("/seed/sessions")
    assert empty.status_code == 200
    assert empty.json() == []


# --- CORS --------------------------------------------------------------


def test_cors_allows_configured_origin():
    from mirage_ai.settings import DEFAULT_SETTINGS

    if not DEFAULT_SETTINGS.cors_origins:
        pytest.skip("no configured origins to test against")
    origin = DEFAULT_SETTINGS.cors_origins[0]
    store = InMemorySessionStore()
    app.dependency_overrides[get_store] = lambda: store
    client = TestClient(app)
    resp = client.options(
        "/sessions",
        headers={"Origin": origin, "Access-Control-Request-Method": "POST"},
    )
    assert resp.headers.get("access-control-allow-origin") == origin
    app.dependency_overrides.clear()


def test_cors_rejects_unconfigured_origin():
    store = InMemorySessionStore()
    app.dependency_overrides[get_store] = lambda: store
    client = TestClient(app)
    resp = client.options(
        "/sessions",
        headers={"Origin": "http://evil.example.com", "Access-Control-Request-Method": "POST"},
    )
    assert "access-control-allow-origin" not in resp.headers
    app.dependency_overrides.clear()
