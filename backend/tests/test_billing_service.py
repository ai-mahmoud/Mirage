import json
from datetime import datetime, timedelta, timezone

import pytest

from mirage_backend import auth, billing_service, session_service
from mirage_backend.billing_client import WebhookVerificationError
from mirage_backend.database import InterviewSessionRow, Organization, make_engine, make_session_factory
from mirage_backend.schemas import SessionCreate

from .fakes import FakeAiClient, FakeStripeClient, sign_stripe_payload


@pytest.fixture
def db():
    engine = make_engine("sqlite:///:memory:")
    factory = make_session_factory(engine)
    session = factory()
    yield session
    session.close()


@pytest.fixture
def stripe():
    return FakeStripeClient()


@pytest.fixture
def ai():
    return FakeAiClient()


@pytest.fixture
def user(db):
    return auth.signup(db, "Acme Inc", "ada@acme.com", "password123")


@pytest.fixture
def org(user):
    return user.organization


def _create(db, ai, user, **overrides):
    defaults = dict(candidate_name="Ada")
    defaults.update(overrides)
    return session_service.create_session(db, ai, SessionCreate(**defaults), user.org_id, user.user_id)


# --- check_session_limit -----------------------------------------------


def test_free_tier_blocks_creation_past_its_limit(db, ai, user, org):
    limit = billing_service.PLAN_LIMITS["free"]
    for _ in range(limit):
        _create(db, ai, user)

    with pytest.raises(billing_service.PlanLimitExceeded):
        _create(db, ai, user, candidate_name="One Too Many")


def test_pro_tier_has_no_limit(db, ai, user, org):
    org.plan_tier = "pro"
    db.commit()
    limit = billing_service.PLAN_LIMITS["free"]
    for i in range(limit + 3):
        _create(db, ai, user, candidate_name=f"Candidate {i}")
    # no exception — pro is unlimited


def test_limit_only_counts_the_current_calendar_month(db, ai, user, org):
    limit = billing_service.PLAN_LIMITS["free"]
    last_month = datetime.now(timezone.utc).replace(day=1) - timedelta(days=1)
    for _ in range(limit):
        row = InterviewSessionRow(
            ai_session_id="ai-old",
            org_id=org.org_id,
            candidate_name="Old",
            interview_type="Technical Interview",
            created_at=last_month,
        )
        db.add(row)
    db.commit()

    # A full free-tier quota of *last* month's sessions shouldn't count
    # against this month's limit.
    _create(db, ai, user, candidate_name="Fresh Month")


def test_unknown_org_raises_organization_not_found(db):
    with pytest.raises(billing_service.OrganizationNotFound):
        billing_service.check_session_limit(db, "does-not-exist")


# --- start_checkout / start_billing_portal ------------------------------


def test_start_checkout_creates_a_stripe_customer_on_first_call(db, stripe, org):
    url = billing_service.start_checkout(db, stripe, org.org_id, "ada@acme.com", "price_pro_123")
    assert url.startswith("https://checkout.stripe.test/")
    assert org.stripe_customer_id is not None
    assert stripe.customers[org.stripe_customer_id]["email"] == "ada@acme.com"
    assert stripe.checkout_calls[0]["price_id"] == "price_pro_123"


def test_start_checkout_reuses_the_existing_stripe_customer(db, stripe, org):
    billing_service.start_checkout(db, stripe, org.org_id, "ada@acme.com", "price_pro_123")
    first_customer_id = org.stripe_customer_id

    billing_service.start_checkout(db, stripe, org.org_id, "ada@acme.com", "price_pro_123")
    assert org.stripe_customer_id == first_customer_id
    assert len(stripe.customers) == 1


def test_billing_portal_requires_an_existing_stripe_customer(db, stripe, org):
    with pytest.raises(billing_service.NoStripeCustomer):
        billing_service.start_billing_portal(db, stripe, org.org_id)


def test_billing_portal_succeeds_after_checkout(db, stripe, org):
    billing_service.start_checkout(db, stripe, org.org_id, "ada@acme.com", "price_pro_123")
    url = billing_service.start_billing_portal(db, stripe, org.org_id)
    assert url.startswith("https://billing.stripe.test/")


# --- apply_webhook_event -------------------------------------------------


def _checkout_completed_event(customer_id: str) -> dict:
    return {"type": "checkout.session.completed", "data": {"object": {"customer": customer_id}}}


def test_checkout_completed_upgrades_org_to_pro(db, stripe, org):
    billing_service.start_checkout(db, stripe, org.org_id, "ada@acme.com", "price_pro_123")
    billing_service.apply_webhook_event(db, _checkout_completed_event(org.stripe_customer_id))
    assert org.plan_tier == "pro"
    assert org.subscription_status == "active"


def test_subscription_updated_to_past_due_keeps_pro_but_records_status(db, stripe, org):
    billing_service.start_checkout(db, stripe, org.org_id, "ada@acme.com", "price_pro_123")
    billing_service.apply_webhook_event(db, _checkout_completed_event(org.stripe_customer_id))

    event = {
        "type": "customer.subscription.updated",
        "data": {"object": {"customer": org.stripe_customer_id, "status": "past_due"}},
    }
    billing_service.apply_webhook_event(db, event)
    assert org.plan_tier == "pro"
    assert org.subscription_status == "past_due"


def test_subscription_updated_to_canceled_status_downgrades_to_free(db, stripe, org):
    billing_service.start_checkout(db, stripe, org.org_id, "ada@acme.com", "price_pro_123")
    billing_service.apply_webhook_event(db, _checkout_completed_event(org.stripe_customer_id))

    event = {
        "type": "customer.subscription.updated",
        "data": {"object": {"customer": org.stripe_customer_id, "status": "canceled"}},
    }
    billing_service.apply_webhook_event(db, event)
    assert org.plan_tier == "free"
    assert org.subscription_status == "canceled"


def test_subscription_deleted_downgrades_to_free(db, stripe, org):
    billing_service.start_checkout(db, stripe, org.org_id, "ada@acme.com", "price_pro_123")
    billing_service.apply_webhook_event(db, _checkout_completed_event(org.stripe_customer_id))

    event = {"type": "customer.subscription.deleted", "data": {"object": {"customer": org.stripe_customer_id}}}
    billing_service.apply_webhook_event(db, event)
    assert org.plan_tier == "free"
    assert org.subscription_status == "canceled"


def test_event_for_unknown_customer_is_a_silent_no_op(db):
    # Must not raise — a webhook endpoint that 500s on a customer_id that
    # isn't ours (or predates this deployment) just makes Stripe retry
    # forever.
    billing_service.apply_webhook_event(db, _checkout_completed_event("cus_not_ours"))


def test_irrelevant_event_type_is_ignored(db, stripe, org):
    billing_service.start_checkout(db, stripe, org.org_id, "ada@acme.com", "price_pro_123")
    original_tier = org.plan_tier
    billing_service.apply_webhook_event(
        db, {"type": "invoice.paid", "data": {"object": {"customer": org.stripe_customer_id}}}
    )
    assert org.plan_tier == original_tier


# --- webhook signature verification (real crypto, via FakeStripeClient) --


def test_valid_signature_is_accepted(stripe):
    payload = json.dumps({"type": "checkout.session.completed", "data": {"object": {}}}).encode()
    header = sign_stripe_payload(payload, "whsec_test_secret")
    event = stripe.construct_webhook_event(payload=payload, signature_header=header, webhook_secret="whsec_test_secret")
    assert event["type"] == "checkout.session.completed"


def test_tampered_payload_is_rejected(stripe):
    payload = json.dumps({"type": "checkout.session.completed"}).encode()
    header = sign_stripe_payload(payload, "whsec_test_secret")
    tampered = payload.replace(b"checkout", b"XXXXXXXX")
    with pytest.raises(WebhookVerificationError):
        stripe.construct_webhook_event(payload=tampered, signature_header=header, webhook_secret="whsec_test_secret")


def test_wrong_secret_is_rejected(stripe):
    payload = json.dumps({"type": "checkout.session.completed"}).encode()
    header = sign_stripe_payload(payload, "whsec_correct")
    with pytest.raises(WebhookVerificationError):
        stripe.construct_webhook_event(payload=payload, signature_header=header, webhook_secret="whsec_wrong")


def test_missing_signature_is_rejected(stripe):
    payload = json.dumps({"type": "checkout.session.completed"}).encode()
    with pytest.raises(WebhookVerificationError):
        stripe.construct_webhook_event(payload=payload, signature_header="", webhook_secret="whsec_test_secret")
