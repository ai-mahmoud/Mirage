import dataclasses
import json

import pytest
from fastapi.testclient import TestClient

import mirage_backend.main as main_module
from mirage_backend.database import make_engine, make_session_factory
from mirage_backend.main import app, get_ai_client, get_db, get_reports_dir, get_stripe_client

from .fakes import FakeAiClient, FakeStripeClient, sign_stripe_payload

WEBHOOK_SECRET = "whsec_test_secret"


@pytest.fixture
def stripe():
    return FakeStripeClient()


@pytest.fixture
def client(tmp_path, stripe, monkeypatch):
    engine = make_engine("sqlite:///:memory:")
    factory = make_session_factory(engine)

    def _get_db():
        db = factory()
        try:
            yield db
        finally:
            db.close()

    # Config is a frozen dataclass — swap the module-level DEFAULT_CONFIG
    # main.py reads from (dataclasses.replace, not attribute mutation)
    # rather than trying to patch individual fields on a frozen instance.
    monkeypatch.setattr(
        main_module,
        "DEFAULT_CONFIG",
        dataclasses.replace(
            main_module.DEFAULT_CONFIG, stripe_price_id_pro="price_pro_123", stripe_webhook_secret=WEBHOOK_SECRET
        ),
    )

    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[get_ai_client] = lambda: FakeAiClient()
    app.dependency_overrides[get_reports_dir] = lambda: str(tmp_path)
    app.dependency_overrides[get_stripe_client] = lambda: stripe
    yield TestClient(app)
    app.dependency_overrides.clear()


def _signup_and_token(client, email="ada@acme.com") -> str:
    resp = client.post("/auth/signup", json={"orgName": "Acme", "email": email, "password": "password123"})
    return resp.json()["accessToken"]


def test_checkout_requires_auth(client):
    resp = client.post("/billing/checkout", json={"plan": "pro"})
    assert resp.status_code == 401


def test_checkout_returns_a_redirect_url(client):
    token = _signup_and_token(client)
    resp = client.post(
        "/billing/checkout", json={"plan": "pro"}, headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    assert resp.json()["url"].startswith("https://checkout.stripe.test/")


def test_billing_portal_requires_a_prior_checkout(client):
    token = _signup_and_token(client)
    resp = client.post("/billing/portal", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 404


def test_billing_portal_succeeds_after_checkout(client):
    token = _signup_and_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    client.post("/billing/checkout", json={"plan": "pro"}, headers=headers)
    resp = client.post("/billing/portal", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["url"].startswith("https://billing.stripe.test/")


def test_get_my_organization_reports_plan_tier(client):
    token = _signup_and_token(client)
    resp = client.get("/organizations/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["planTier"] == "free"


def test_webhook_upgrades_org_after_checkout_completes(client):
    token = _signup_and_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    client.post("/billing/checkout", json={"plan": "pro"}, headers=headers)
    customer_id = client.get("/organizations/me", headers=headers).json()  # noqa: F841 - just to prove org exists

    # Pull the customer id the checkout call actually used, straight from
    # the fake (mirrors how a real test would inspect what was sent to Stripe).
    stripe = main_module.app.dependency_overrides[get_stripe_client]()
    real_customer_id = next(iter(stripe.customers))

    payload = json.dumps(
        {"type": "checkout.session.completed", "data": {"object": {"customer": real_customer_id}}}
    ).encode()
    sig = sign_stripe_payload(payload, WEBHOOK_SECRET)
    resp = client.post("/billing/webhook", content=payload, headers={"Stripe-Signature": sig})
    assert resp.status_code == 200

    org_resp = client.get("/organizations/me", headers=headers)
    assert org_resp.json()["planTier"] == "pro"
    assert org_resp.json()["subscriptionStatus"] == "active"


def test_webhook_rejects_bad_signature(client):
    payload = json.dumps({"type": "checkout.session.completed", "data": {"object": {}}}).encode()
    resp = client.post("/billing/webhook", content=payload, headers={"Stripe-Signature": "t=1,v1=bogus"})
    assert resp.status_code == 400


def test_billing_disabled_returns_503_when_unconfigured(tmp_path):
    """A separate client that leaves get_stripe_client wired to the real
    dependency — with no BACKEND_STRIPE_SECRET_KEY set (the test
    environment's actual default), every /billing/* route should fail
    closed with a clear 503, not a crash."""
    engine = make_engine("sqlite:///:memory:")
    factory = make_session_factory(engine)

    def _get_db():
        db = factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[get_ai_client] = lambda: FakeAiClient()
    app.dependency_overrides[get_reports_dir] = lambda: str(tmp_path)
    # get_stripe_client deliberately NOT overridden here.
    no_raise_client = TestClient(app)
    try:
        token = _signup_and_token(no_raise_client, email="billing-off@acme.com")
        resp = no_raise_client.post(
            "/billing/checkout", json={"plan": "pro"}, headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 503
    finally:
        app.dependency_overrides.clear()


def test_plan_limit_exceeded_returns_402(client):
    from mirage_backend import billing_service

    token = _signup_and_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    limit = billing_service.PLAN_LIMITS["free"]
    for _ in range(limit):
        resp = client.post("/sessions", json={"candidateName": "Ada"}, headers=headers)
        assert resp.status_code == 200
    resp = client.post("/sessions", json={"candidateName": "One Too Many"}, headers=headers)
    assert resp.status_code == 402
