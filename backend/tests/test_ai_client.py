"""HttpAiClient tests use httpx.MockTransport so no real ai/ process needs
to be running — each test asserts the request HttpAiClient builds and
feeds it a canned response."""

import json

import httpx

from mirage_backend.ai_client import HttpAiClient


def _client(handler) -> HttpAiClient:
    return HttpAiClient("http://ai.test", transport=httpx.MockTransport(handler))


def test_create_session_posts_payload_and_returns_id():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/sessions"
        payload = json.loads(request.content)
        assert payload == {
            "candidateName": "Ada",
            "observerName": "Bob",
            "position": None,
            "department": None,
            "interviewType": "Technical Interview",
        }
        return httpx.Response(200, json={"sessionId": "abc123", "startedAt": 0.0, "demo": False})

    client = _client(handler)
    session_id = client.create_session(
        candidate_name="Ada", observer_name="Bob", position=None, department=None, interview_type="Technical Interview"
    )
    assert session_id == "abc123"


def test_post_events_sends_batch_and_returns_snapshot():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/sessions/abc123/events"
        payload = json.loads(request.content)
        assert payload == {"events": [{"type": "mouse_click", "t": 1.0}]}
        return httpx.Response(200, json={"sessionId": "abc123", "trustDna": {"overall": 71.0}})

    client = _client(handler)
    snapshot = client.post_events("abc123", [{"type": "mouse_click", "t": 1.0}])
    assert snapshot["trustDna"]["overall"] == 71.0


def test_get_snapshot_requests_correct_path():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/sessions/abc123"
        return httpx.Response(200, json={"sessionId": "abc123"})

    client = _client(handler)
    assert client.get_snapshot("abc123") == {"sessionId": "abc123"}


def test_get_report_requests_correct_path():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/sessions/abc123/report"
        return httpx.Response(200, json={"sessionId": "abc123", "executiveSummary": "…"})

    client = _client(handler)
    assert client.get_report("abc123")["executiveSummary"] == "…"


def test_raises_on_http_error_status():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"detail": "not found"})

    client = _client(handler)
    try:
        client.get_snapshot("missing")
    except httpx.HTTPStatusError:
        pass
    else:
        raise AssertionError("expected HTTPStatusError")
