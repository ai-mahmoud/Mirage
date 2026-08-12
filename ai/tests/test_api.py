"""API-layer tests for the observability behavior added in Phase 4
(request-id correlation, the generic 500 handler, health degradation).
Session-route coverage (create/ingest/get/report/delete) is Phase 5's
job — this file is deliberately narrow.
"""

from fastapi.testclient import TestClient

from mirage_ai.api import app, get_store
from mirage_ai.store import InMemorySessionStore


class BrokenStore:
    """A store that fails every call — for exercising failure paths
    without needing a real broken database."""

    def get(self, session_id):
        raise RuntimeError("boom")

    def save(self, engine):
        raise RuntimeError("boom")

    def delete(self, session_id):
        raise RuntimeError("boom")

    def list_ids(self):
        raise RuntimeError("boom")

    def ping(self):
        raise RuntimeError("db down")


def _client(store) -> TestClient:
    app.dependency_overrides[get_store] = lambda: store
    return TestClient(app)


def test_health_check_reports_database_connectivity():
    client = _client(InMemorySessionStore())
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "database": "connected"}
    app.dependency_overrides.clear()


def test_health_check_returns_503_when_store_unreachable():
    client = _client(BrokenStore())
    resp = client.get("/health")
    assert resp.status_code == 503
    assert resp.json() == {"status": "degraded", "database": "unreachable"}
    app.dependency_overrides.clear()


def test_every_response_carries_a_request_id_header():
    client = _client(InMemorySessionStore())
    resp = client.get("/health")
    assert resp.headers.get("x-request-id")
    app.dependency_overrides.clear()


def test_unhandled_exception_returns_generic_500_with_request_id():
    app.dependency_overrides[get_store] = lambda: BrokenStore()
    # See backend/tests/test_main_api.py's identical test for why
    # raise_server_exceptions=False is needed to observe the handler's
    # response rather than the original exception.
    no_raise_client = TestClient(app, raise_server_exceptions=False)
    resp = no_raise_client.get("/sessions/whatever")
    assert resp.status_code == 500
    body = resp.json()
    assert body["detail"] == "Internal server error"
    assert body["requestId"]
    assert body["requestId"] == resp.headers["x-request-id"]
    app.dependency_overrides.clear()
