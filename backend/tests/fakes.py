"""FakeAiClient: a hand-written AiClient test double.

Purpose: let session_service / API tests exercise the full flow without a
real ai/ process. It reproduces just enough of the ai/ engine's observable
behavior — trust drops once enough events have been recorded, and any
evidence injected via `inject_evidence` shows up in the next snapshot — to
test the backend's own mirroring logic. It does not re-test the ai/
engine's signal/evidence reasoning; that is ai/'s own test suite's job.
"""

from __future__ import annotations

import itertools

_ids = itertools.count(1)


class FakeAiClient:
    def __init__(self) -> None:
        self._sessions: dict[str, dict] = {}

    def create_session(self, *, candidate_name, observer_name, position, department, interview_type) -> str:
        """create_session: ... -> String
        Purpose: mint a fresh fake ai/ session id and start tracking its state.
        """
        session_id = f"ai-{next(_ids)}"
        self._sessions[session_id] = {"events": 0, "evidence": []}
        return session_id

    def post_events(self, ai_session_id: str, events: list[dict]) -> dict:
        """post_events: String (list-of dict) -> dict
        Purpose: record `events` against the session and return the
        resulting fake snapshot (see _snapshot_for).
        """
        self._sessions[ai_session_id]["events"] += len(events)
        return self._snapshot_for(ai_session_id)

    def get_snapshot(self, ai_session_id: str) -> dict:
        return self._snapshot_for(ai_session_id)

    def get_report(self, ai_session_id: str) -> dict:
        snapshot = self._snapshot_for(ai_session_id)
        return {
            "sessionId": ai_session_id,
            "candidateName": "Demo Candidate",
            "observerName": "Interviewer",
            "position": None,
            "department": None,
            "interviewType": "Technical Interview",
            "startedAt": 0.0,
            "endedAt": 1.0,
            "durationMs": 1.0,
            "generatedAt": 1.0,
            "executiveSummary": "Fake summary.",
            "trustDna": snapshot["trustDna"],
            "trustDnaHistory": [{"t": 0.0, "overall": snapshot["trustDna"]["overall"]}],
            "confidence": snapshot["confidence"],
            "recommendation": snapshot["recommendation"],
            "evidence": snapshot["evidence"],
            "timeline": [],
            "privacyStatement": ["No keystroke content was collected."],
        }

    def inject_evidence(self, ai_session_id: str, card: dict) -> None:
        """Test helper (not part of AiClient): make the next snapshot for
        `ai_session_id` include `card`."""
        self._sessions[ai_session_id]["evidence"].append(card)

    def _snapshot_for(self, ai_session_id: str) -> dict:
        """_snapshot_for: String -> dict
        Purpose: the fake SessionSnapshot for a session: Trust DNA drops
        below 45 once 30+ events have been recorded, driving the same
        recommendation ladder the real ai/ engine uses.
        """
        state = self._sessions[ai_session_id]
        events = state["events"]
        overall = 75.0 if events < 30 else 30.0
        if events < 25:
            status, label = "evidence_insufficient", "Insufficient Evidence"
        elif overall < 45:
            status, label = "manual_review_recommended", "Manual Review Recommended"
        else:
            status, label = "continue_monitoring", "Continue Monitoring"
        dimensions = [
            {"id": dim_id, "label": dim_id.replace("_", " ").title(), "score": overall, "confidence": 1.0, "trend": "stable"}
            for dim_id in (
                "behavioral_consistency",
                "interaction_naturalness",
                "attention_stability",
                "context_integrity",
                "adaptive_responsiveness",
                "session_authenticity",
            )
        ]
        return {
            "sessionId": ai_session_id,
            "status": "live",
            "startedAt": 0.0,
            "elapsedMs": float(events),
            "trustDna": {"dimensions": dimensions, "overall": overall},
            "liveSignals": [],
            "evidence": state["evidence"],
            "confidence": {"evidenceConfidence": 0.9, "recommendationConfidence": 0.9, "drivers": []},
            "recommendation": {
                "status": status,
                "label": label,
                "reasons": ["fake reason"],
                "suggestedAction": "fake action",
                "humanReviewRequired": status == "manual_review_recommended",
            },
            "currentRisk": "review" if status == "manual_review_recommended" else "low",
            "timeline": [],
        }
