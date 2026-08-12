"""REST API — Mirage Backend.

Thin HTTP layer only: every route validates/parses request data via
schemas.py, then delegates to session_service.py (or auth.py, for the
/auth/* routes) for the actual world-state transition. Run with:

    uvicorn mirage_backend.main:app --reload
"""

from __future__ import annotations

import logging

import httpx
from fastapi import Depends, FastAPI, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy import text
from sqlalchemy.orm import Session as DBSession

from . import auth, session_service
from .ai_client import AiClient, HttpAiClient
from .config import DEFAULT_CONFIG
from .database import User, make_engine, make_session_factory
from .logging_config import configure_logging
from .pdf_service import render_report
from .request_context import RequestIdMiddleware, get_request_id
from .schemas import (
    EventBatch,
    LoginRequest,
    SessionCreate,
    SessionReportOut,
    SessionResponse,
    SignupRequest,
    TokenResponse,
    TrustStatusResponse,
    UserResponse,
)

configure_logging()
logger = logging.getLogger("mirage_backend")

if DEFAULT_CONFIG.sentry_dsn:
    import sentry_sdk

    sentry_sdk.init(dsn=DEFAULT_CONFIG.sentry_dsn, environment=DEFAULT_CONFIG.environment, traces_sample_rate=0.1)

app = FastAPI(
    title="Mirage Backend",
    version="0.1.0",
    # /docs, /redoc, and the raw OpenAPI schema are dev conveniences, not
    # something a production deployment should expose to the internet.
    docs_url="/docs" if DEFAULT_CONFIG.environment != "production" else None,
    redoc_url="/redoc" if DEFAULT_CONFIG.environment != "production" else None,
    openapi_url="/openapi.json" if DEFAULT_CONFIG.environment != "production" else None,
)
app.add_middleware(
    CORSMiddleware, allow_origins=DEFAULT_CONFIG.cors_origins, allow_methods=["*"], allow_headers=["*"]
)
app.add_middleware(RequestIdMiddleware)

# Rate limiting: credential-guessing and session-flooding are the two
# things worth throttling here. Keyed by remote address — coarse, but
# this is a single-instance deployment with no trusted proxy chain to
# parse X-Forwarded-For from yet (revisit once behind a real LB).
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Built lazily (on first real get_db() call) rather than at import time —
# importing this module must not require a live database connection, since
# tests override get_db entirely via app.dependency_overrides and never
# invoke this one at all.
_session_factory = None
_ai_client: AiClient = HttpAiClient(DEFAULT_CONFIG.ai_service_url)


def _get_session_factory():
    global _session_factory
    if _session_factory is None:
        engine = make_engine(DEFAULT_CONFIG.database_url)
        _session_factory = make_session_factory(engine)
    return _session_factory


def get_db():
    db = _get_session_factory()()
    try:
        yield db
    finally:
        db.close()


def get_ai_client() -> AiClient:
    return _ai_client


def get_reports_dir() -> str:
    return DEFAULT_CONFIG.reports_dir


def get_current_user(
    authorization: str | None = Header(default=None), db: DBSession = Depends(get_db)
) -> User:
    """get_current_user: [String] DBSession -> User
    Purpose: the auth dependency every /sessions* route requires — decode
    the bearer JWT from the Authorization header, look up the User it
    names, or raise AuthenticationError (401). This is what makes every
    session route org-scoped: routes read `user.org_id` from here rather
    than trusting anything the client sends.
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        raise auth.AuthenticationError("missing bearer token")
    token = authorization.split(" ", 1)[1].strip()
    payload = auth.decode_access_token(token, DEFAULT_CONFIG.jwt_secret_key)
    user = db.get(User, payload.get("sub"))
    if user is None:
        raise auth.AuthenticationError("user no longer exists")
    return user


@app.exception_handler(session_service.SessionNotFound)
def handle_session_not_found(request: Request, exc: session_service.SessionNotFound) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": f"Session not found: {exc}"})


@app.exception_handler(auth.AuthenticationError)
def handle_authentication_error(request: Request, exc: auth.AuthenticationError) -> JSONResponse:
    return JSONResponse(status_code=401, content={"detail": str(exc)})


@app.exception_handler(auth.AuthorizationError)
def handle_authorization_error(request: Request, exc: auth.AuthorizationError) -> JSONResponse:
    return JSONResponse(status_code=403, content={"detail": str(exc)})


@app.exception_handler(auth.EmailAlreadyRegistered)
def handle_email_already_registered(request: Request, exc: auth.EmailAlreadyRegistered) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": f"Email already registered: {exc}"})


@app.exception_handler(httpx.HTTPError)
def handle_ai_service_error(request: Request, exc: httpx.HTTPError) -> JSONResponse:
    # Without this handler an AI-service failure escapes as an unhandled 500,
    # whose response bypasses the CORS middleware — the browser then reports a
    # misleading "blocked by CORS policy" instead of the real cause.
    logger.warning("ai/ service error: %s: %s", type(exc).__name__, exc)
    return JSONResponse(
        status_code=502,
        content={"detail": f"AI service unreachable or failing ({type(exc).__name__}): {exc}"},
    )


@app.exception_handler(Exception)
def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    # Catch-all: everything above is a known, named failure mode with its
    # own handler. Anything reaching here is a genuine bug — log the full
    # traceback (Sentry, if configured, captures it too) and return a
    # generic body with the correlation id so a support conversation has
    # something to search logs by, without leaking internals to the client.
    #
    # FastAPI routes bare-`Exception` handlers through Starlette's
    # ServerErrorMiddleware, which sits outside RequestIdMiddleware — so
    # the response header that middleware would normally inject never
    # applies here; set it explicitly. request.state.request_id (set
    # directly on the ASGI scope) is used over get_request_id() since
    # it's guaranteed present regardless of exactly where in the
    # middleware stack this handler ends up running.
    request_id = getattr(request.state, "request_id", None) or get_request_id()
    logger.exception("unhandled exception")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "requestId": request_id},
        headers={"X-Request-ID": request_id},
    )


@app.get("/health")
def health(db: DBSession = Depends(get_db)) -> JSONResponse:
    """Liveness AND readiness: a plain "the process is up" response was
    fine for a single-container demo, but a healthcheck that can't tell
    "process up, database unreachable" from "everything's fine" is
    useless for orchestration/alerting once this is a real deployment."""
    try:
        db.execute(text("SELECT 1"))
        return JSONResponse(status_code=200, content={"status": "ok", "database": "connected"})
    except Exception as exc:  # noqa: BLE001 - any DB failure means "not ready"
        logger.error("health check: database unreachable: %s", exc)
        return JSONResponse(status_code=503, content={"status": "degraded", "database": "unreachable"})


# --- Auth ----------------------------------------------------------------


@app.post("/auth/signup", response_model=TokenResponse)
@limiter.limit("20/minute")
def signup(request: Request, payload: SignupRequest, db: DBSession = Depends(get_db)) -> TokenResponse:
    user = auth.signup(db, payload.org_name, payload.email, payload.password)
    token = auth.create_access_token(user, DEFAULT_CONFIG.jwt_secret_key)
    logger.info("org signed up: org_id=%s user_id=%s", user.org_id, user.user_id)
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@app.post("/auth/login", response_model=TokenResponse)
@limiter.limit("20/minute")
def login(request: Request, payload: LoginRequest, db: DBSession = Depends(get_db)) -> TokenResponse:
    user = auth.login(db, payload.email, payload.password)
    token = auth.create_access_token(user, DEFAULT_CONFIG.jwt_secret_key)
    logger.info("user logged in: org_id=%s user_id=%s", user.org_id, user.user_id)
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@app.post("/auth/logout")
def logout() -> dict:
    # JWTs are stateless — "logout" is the client discarding its token,
    # there's no server-side session to invalidate. A deny-list keyed by
    # token id would be a Phase 3 addition if revocation becomes necessary.
    return {"status": "logged_out"}


@app.get("/auth/me", response_model=UserResponse)
def get_me(user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(user)


# --- Sessions (every route below is scoped to the caller's own org) ------


@app.post("/sessions", response_model=SessionResponse)
@limiter.limit("30/minute")
def create_session(
    request: Request,
    payload: SessionCreate,
    db: DBSession = Depends(get_db),
    ai: AiClient = Depends(get_ai_client),
    user: User = Depends(get_current_user),
) -> SessionResponse:
    return session_service.create_session(db, ai, payload, user.org_id)


@app.get("/sessions", response_model=list[SessionResponse])
def list_sessions(
    db: DBSession = Depends(get_db), user: User = Depends(get_current_user)
) -> list[SessionResponse]:
    return session_service.list_sessions(db, user.org_id)


@app.post("/sessions/{session_id}/events", response_model=TrustStatusResponse)
def post_events(
    session_id: str,
    batch: EventBatch,
    db: DBSession = Depends(get_db),
    ai: AiClient = Depends(get_ai_client),
    user: User = Depends(get_current_user),
) -> TrustStatusResponse:
    session_service.record_events(db, ai, session_id, batch.events, user.org_id)
    return session_service.current_status(db, ai, session_id, user.org_id)


@app.get("/sessions/{session_id}/trust", response_model=TrustStatusResponse)
def get_trust(
    session_id: str,
    db: DBSession = Depends(get_db),
    ai: AiClient = Depends(get_ai_client),
    user: User = Depends(get_current_user),
) -> TrustStatusResponse:
    return session_service.current_status(db, ai, session_id, user.org_id)


@app.post("/sessions/{session_id}/end", response_model=SessionResponse)
def end_session(
    session_id: str,
    db: DBSession = Depends(get_db),
    ai: AiClient = Depends(get_ai_client),
    user: User = Depends(get_current_user),
) -> SessionResponse:
    return session_service.end_session(db, ai, session_id, user.org_id)


@app.get("/sessions/{session_id}/report", response_model=SessionReportOut)
def get_report(
    session_id: str,
    db: DBSession = Depends(get_db),
    ai: AiClient = Depends(get_ai_client),
    user: User = Depends(get_current_user),
) -> SessionReportOut:
    return session_service.report_out(db, ai, session_id, user.org_id)


@app.get("/sessions/{session_id}/report/pdf")
def get_report_pdf(
    session_id: str,
    db: DBSession = Depends(get_db),
    ai: AiClient = Depends(get_ai_client),
    reports_dir: str = Depends(get_reports_dir),
    user: User = Depends(get_current_user),
):
    report = session_service.build_report(db, ai, session_id, user.org_id)
    file_path = render_report(report, reports_dir=reports_dir)
    return FileResponse(file_path, media_type="application/pdf", filename=f"session_{session_id}_report.pdf")
