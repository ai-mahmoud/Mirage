"""The boundary to the ai/ service (see ai/README.md for the contract this
module speaks).

Data definition
---------------
`AiClient` is the interface the rest of the backend programs against —
never call `httpx` directly outside this module. Two implementations
exist: `HttpAiClient` (talks to a real ai/ process) and, in tests, a
hand-written `FakeAiClient` (tests/fakes.py). Every method returns the
plain camelCase dict the ai/ service returns on the wire — the backend
reads specific keys out of it in session_service.py rather than adding a
second parsing model for data that already has one on the ai/ side.
"""

from __future__ import annotations

from typing import Protocol

import httpx


class AiClient(Protocol):
    def create_session(
        self,
        *,
        candidate_name: str,
        observer_name: str,
        position: str | None,
        department: str | None,
        interview_type: str | None,
    ) -> str:
        """-> the ai/ service's session_id for the newly created session."""
        ...

    def post_events(self, ai_session_id: str, events: list[dict]) -> dict:
        """-> the resulting SessionSnapshot (dict) after ingesting `events`."""
        ...

    def get_snapshot(self, ai_session_id: str) -> dict:
        """-> the current SessionSnapshot (dict)."""
        ...

    def get_report(self, ai_session_id: str) -> dict:
        """-> the final SessionReport (dict)."""
        ...


class HttpAiClient:
    """HttpAiClient: String [timeout: Number] [transport: httpx.BaseTransport] -> AiClient
    Purpose: talk to a real ai/ FastAPI process at `base_url` over HTTP.
    `transport` is exposed only so tests can inject an httpx.MockTransport
    instead of hitting the network (see tests/test_ai_client.py).
    """

    def __init__(self, base_url: str, timeout: float = 5.0, transport: httpx.BaseTransport | None = None) -> None:
        self._client = httpx.Client(base_url=base_url, timeout=timeout, transport=transport)

    def create_session(
        self,
        *,
        candidate_name: str,
        observer_name: str,
        position: str | None,
        department: str | None,
        interview_type: str | None,
    ) -> str:
        resp = self._client.post(
            "/sessions",
            json={
                "candidateName": candidate_name,
                "observerName": observer_name,
                "position": position,
                "department": department,
                "interviewType": interview_type,
            },
        )
        resp.raise_for_status()
        return resp.json()["sessionId"]

    def post_events(self, ai_session_id: str, events: list[dict]) -> dict:
        resp = self._client.post(f"/sessions/{ai_session_id}/events", json={"events": events})
        resp.raise_for_status()
        return resp.json()

    def get_snapshot(self, ai_session_id: str) -> dict:
        resp = self._client.get(f"/sessions/{ai_session_id}")
        resp.raise_for_status()
        return resp.json()

    def get_report(self, ai_session_id: str) -> dict:
        resp = self._client.get(f"/sessions/{ai_session_id}/report")
        resp.raise_for_status()
        return resp.json()
