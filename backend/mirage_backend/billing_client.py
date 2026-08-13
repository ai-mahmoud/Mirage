"""The boundary to Stripe. Mirrors ai_client.py's shape: `StripeClient` is
the interface the rest of the backend programs against — never import the
`stripe` SDK directly outside this module. Two implementations exist:
`RealStripeClient` (talks to Stripe's real API) and, in tests, a
hand-written `FakeStripeClient` (tests/fakes.py).
"""

from __future__ import annotations

from typing import Protocol


class WebhookVerificationError(Exception):
    """Raised when a POST /billing/webhook payload's signature doesn't
    verify — i.e. it didn't actually come from Stripe."""


class BillingNotConfigured(Exception):
    """Raised when a billing route is called but BACKEND_STRIPE_SECRET_KEY
    isn't set — the deployment simply hasn't turned billing on yet,
    distinct from any Stripe-side failure."""


class StripeClient(Protocol):
    def create_customer(self, *, email: str, org_id: str) -> str:
        """-> a new Stripe customer id for `email`, tagged with org_id in
        metadata so a webhook event can be traced back to an Organization
        even before the local row is updated."""
        ...

    def create_checkout_session(
        self, *, customer_id: str, price_id: str, success_url: str, cancel_url: str
    ) -> str:
        """-> the URL to redirect the browser to for a subscription
        checkout."""
        ...

    def create_billing_portal_session(self, *, customer_id: str, return_url: str) -> str:
        """-> the URL to redirect the browser to for Stripe's hosted
        billing-management portal (update card, cancel, view invoices)."""
        ...

    def construct_webhook_event(self, *, payload: bytes, signature_header: str, webhook_secret: str) -> dict:
        """-> the verified event dict, or raises WebhookVerificationError.
        This is the one call that must never trust its input without
        verifying it — anyone can POST arbitrary JSON to a webhook URL."""
        ...


class RealStripeClient:
    """RealStripeClient: String -> StripeClient
    Purpose: talk to the real Stripe API using `api_key`. Constructing
    this without a real key still works (the `stripe` SDK doesn't
    validate the key until a call is made) — main.py only constructs
    this when DEFAULT_CONFIG.stripe_secret_key is non-empty, so a demo
    deployment with billing unconfigured never even imports it.
    """

    def __init__(self, api_key: str) -> None:
        import stripe

        self._stripe = stripe
        self._stripe.api_key = api_key

    def create_customer(self, *, email: str, org_id: str) -> str:
        customer = self._stripe.Customer.create(email=email, metadata={"org_id": org_id})
        return customer.id

    def create_checkout_session(
        self, *, customer_id: str, price_id: str, success_url: str, cancel_url: str
    ) -> str:
        session = self._stripe.checkout.Session.create(
            customer=customer_id,
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=success_url,
            cancel_url=cancel_url,
        )
        return session.url

    def create_billing_portal_session(self, *, customer_id: str, return_url: str) -> str:
        session = self._stripe.billing_portal.Session.create(customer=customer_id, return_url=return_url)
        return session.url

    def construct_webhook_event(self, *, payload: bytes, signature_header: str, webhook_secret: str) -> dict:
        try:
            event = self._stripe.Webhook.construct_event(payload, signature_header, webhook_secret)
        except (self._stripe.error.SignatureVerificationError, ValueError) as exc:
            raise WebhookVerificationError(str(exc)) from exc
        return event
