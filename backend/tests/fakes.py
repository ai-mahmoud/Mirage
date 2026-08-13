"""FakeAiClient / FakeStripeClient: hand-written test doubles.

Purpose: let session_service / API tests exercise the full flow without a
real ai/ process or a real Stripe account. FakeAiClient reproduces just
enough of the ai/ engine's observable behavior — trust drops once enough
events have been recorded, and any evidence injected via
`inject_evidence` shows up in the next snapshot — to test the backend's
own mirroring logic. It does not re-test the ai/ engine's signal/evidence
reasoning; that is ai/'s own test suite's job. FakeStripeClient similarly
reproduces just enough of Stripe's observable behavior (issuing
customer/session ids, and — critically — real signature verification, so
webhook tests exercise the same crypto a real attacker would have to
defeat) to test billing_service's own logic.
"""

from __future__ import annotations

import hashlib
import hmac
import itertools
import json
import time

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

    def delete_session(self, ai_session_id: str) -> None:
        self._sessions.pop(ai_session_id, None)

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


def sign_stripe_payload(payload: bytes, secret: str, timestamp: int | None = None) -> str:
    """Test helper: build a real Stripe-Signature header value for
    `payload` signed with `secret` — Stripe's actual v1 HMAC-SHA256
    scheme (timestamp + "." + payload, signed), not a fake shortcut."""
    ts = timestamp if timestamp is not None else int(time.time())
    signed_payload = f"{ts}.".encode() + payload
    signature = hmac.new(secret.encode(), signed_payload, hashlib.sha256).hexdigest()
    return f"t={ts},v1={signature}"


def _verify_stripe_signature(payload: bytes, signature_header: str, secret: str) -> bool:
    """Mirrors Stripe's own verification algorithm exactly — the inverse
    of sign_stripe_payload above."""
    parts = dict(p.split("=", 1) for p in signature_header.split(",") if "=" in p)
    ts, sig = parts.get("t"), parts.get("v1")
    if not ts or not sig:
        return False
    signed_payload = f"{ts}.".encode() + payload
    expected = hmac.new(secret.encode(), signed_payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, sig)


class FakeStripeClient:
    """A StripeClient double: mints predictable customer/checkout/portal
    ids and URLs, and performs REAL signature verification (see
    _verify_stripe_signature) rather than rubber-stamping every payload
    — so webhook tests exercise genuine tamper detection, not just the
    happy path."""

    def __init__(self) -> None:
        self.customers: dict[str, dict] = {}
        self.checkout_calls: list[dict] = []
        self.portal_calls: list[dict] = []

    def create_customer(self, *, email: str, org_id: str) -> str:
        customer_id = f"cus_{next(_ids)}"
        self.customers[customer_id] = {"email": email, "org_id": org_id}
        return customer_id

    def create_checkout_session(self, *, customer_id: str, price_id: str, success_url: str, cancel_url: str) -> str:
        self.checkout_calls.append(
            {"customer_id": customer_id, "price_id": price_id, "success_url": success_url, "cancel_url": cancel_url}
        )
        return f"https://checkout.stripe.test/session/{next(_ids)}"

    def create_billing_portal_session(self, *, customer_id: str, return_url: str) -> str:
        self.portal_calls.append({"customer_id": customer_id, "return_url": return_url})
        return f"https://billing.stripe.test/portal/{next(_ids)}"

    def construct_webhook_event(self, *, payload: bytes, signature_header: str, webhook_secret: str) -> dict:
        from mirage_backend.billing_client import WebhookVerificationError

        if not _verify_stripe_signature(payload, signature_header, webhook_secret):
            raise WebhookVerificationError("signature mismatch")
        return json.loads(payload)
