"""Shared pytest fixtures across the whole backend test suite."""

import pytest


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    """The rate limiter (main.py's `limiter`, slowapi) tracks state on
    the shared `app` object across every test file in one pytest run,
    keyed by remote address — and TestClient always looks like the same
    address ("testclient"). Without a reset, tests that legitimately
    call /auth/signup or /auth/login several times (this suite has many
    across test_auth.py, test_billing_routes.py,
    test_consent_and_data_rights.py, ...) accumulate against the *same*
    20-requests/minute budget a real caller would face, and enough of
    them together start failing with 429 regardless of test order —
    not a real rate-limiting concern, just cross-test interference.
    """
    from mirage_backend.main import limiter

    limiter.reset()
    yield
