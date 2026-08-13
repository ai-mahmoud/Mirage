"""Billing world-state transitions: Stripe checkout/portal session
creation, webhook event handling, and plan-tier usage-limit enforcement.

World data definition
----------------------
An Organization's billing state is its plan_tier + stripe_customer_id +
subscription_status (database.py). Handlers below mirror
session_service.py's shape: each takes the SQLAlchemy DBSession and a
StripeClient explicitly, no module-level globals, so tests supply an
in-memory database and a FakeStripeClient (tests/fakes.py) instead of a
live Stripe account.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session as DBSession

from .billing_client import StripeClient
from .config import DEFAULT_CONFIG
from .database import InterviewSessionRow, Organization


class OrganizationNotFound(Exception):
    """Raised when an org_id doesn't name an existing Organization —
    shouldn't happen in practice (every authenticated request's org_id
    comes from a real User row's FK), but guards against a dangling
    reference rather than crashing with an AttributeError on None."""


class PlanLimitExceeded(Exception):
    """Raised when an org has hit its plan tier's session-creation limit
    for the current billing period."""


class NoStripeCustomer(Exception):
    """Raised by start_billing_portal when the org has no Stripe customer
    yet (never completed a checkout — nothing to manage)."""


# Sessions-per-calendar-month ceiling per plan tier. None means
# unlimited. Calibrated defaults, not scientific constants — recalibrate
# once there's real usage data to price against.
PLAN_LIMITS: dict[str, int | None] = {
    "free": 5,
    "pro": None,
}


def _get_org_or_raise(db: DBSession, org_id: str) -> Organization:
    org = db.get(Organization, org_id)
    if org is None:
        raise OrganizationNotFound(org_id)
    return org


def check_session_limit(db: DBSession, org_id: str) -> None:
    """check_session_limit: DBSession String -> Void
    Purpose: raise PlanLimitExceeded if `org_id` has already created
    PLAN_LIMITS[plan_tier] sessions since the start of the current
    calendar month (UTC). A plan_tier missing from PLAN_LIMITS (should
    never happen — plan_tier only ever comes from "free" or a webhook
    setting "pro") is treated as unlimited rather than raising, so an
    unrecognized tier fails open, not closed.
    """
    org = _get_org_or_raise(db, org_id)
    limit = PLAN_LIMITS.get(org.plan_tier)
    if limit is None:
        return

    period_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    count = (
        db.query(InterviewSessionRow)
        .filter(InterviewSessionRow.org_id == org_id, InterviewSessionRow.created_at >= period_start)
        .count()
    )
    if count >= limit:
        raise PlanLimitExceeded(
            f"org {org_id} has reached its {org.plan_tier} plan's limit of {limit} sessions this month"
        )


def start_checkout(db: DBSession, stripe: StripeClient, org_id: str, user_email: str, price_id: str) -> str:
    """start_checkout: DBSession StripeClient String String String -> String
    Purpose: -> a Stripe Checkout URL for org_id to subscribe to
    `price_id`. Creates (and persists) a Stripe customer for the org on
    first checkout; reuses it on every later one.
    """
    org = _get_org_or_raise(db, org_id)
    if org.stripe_customer_id is None:
        org.stripe_customer_id = stripe.create_customer(email=user_email, org_id=org_id)
        db.commit()

    return stripe.create_checkout_session(
        customer_id=org.stripe_customer_id,
        price_id=price_id,
        success_url=f"{DEFAULT_CONFIG.frontend_base_url}/settings?checkout=success",
        cancel_url=f"{DEFAULT_CONFIG.frontend_base_url}/pricing?checkout=cancelled",
    )


def start_billing_portal(db: DBSession, stripe: StripeClient, org_id: str) -> str:
    """start_billing_portal: DBSession StripeClient String -> String
    Purpose: -> a Stripe billing-portal URL for org_id to manage an
    existing subscription (update card, view invoices, cancel). Raises
    NoStripeCustomer if the org has never checked out.
    """
    org = _get_org_or_raise(db, org_id)
    if org.stripe_customer_id is None:
        raise NoStripeCustomer(org_id)

    return stripe.create_billing_portal_session(
        customer_id=org.stripe_customer_id, return_url=f"{DEFAULT_CONFIG.frontend_base_url}/settings"
    )


def apply_webhook_event(db: DBSession, event: dict) -> None:
    """apply_webhook_event: DBSession dict -> Void
    Purpose: mirror an already-verified Stripe event (see
    billing_client.StripeClient.construct_webhook_event — this function
    never re-checks the signature, it trusts its caller did) onto the
    Organization it concerns. Handles the events that actually change an
    org's plan: checkout completing (-> "pro"/"active"), and the
    subscription lifecycle events Stripe sends afterward. Any other
    event type — Stripe sends dozens this product doesn't act on — is a
    deliberate no-op, and an event for a customer_id that isn't one of
    ours is silently ignored rather than raising, since a webhook
    endpoint that 500s on unrecognized-but-legitimate Stripe traffic
    just causes Stripe to keep retrying it forever.
    """
    event_type = event.get("type")
    obj = event.get("data", {}).get("object", {})
    customer_id = obj.get("customer")
    if customer_id is None:
        return

    org = db.query(Organization).filter(Organization.stripe_customer_id == customer_id).first()
    if org is None:
        return

    if event_type == "checkout.session.completed":
        org.plan_tier = "pro"
        org.subscription_status = "active"
        db.commit()

    elif event_type == "customer.subscription.updated":
        status = obj.get("status", "active")
        org.subscription_status = status
        org.plan_tier = "pro" if status in ("active", "trialing", "past_due") else "free"
        db.commit()

    elif event_type == "customer.subscription.deleted":
        org.subscription_status = "canceled"
        org.plan_tier = "free"
        db.commit()
