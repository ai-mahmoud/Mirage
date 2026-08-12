"""REST API — Mirage Backend.

Thin HTTP layer only: every route validates/parses request data via
schemas.py, then delegates to session_service.py (or auth.py, for the
/auth/* routes) for the actual world-state transition. Run with:

    uvicorn mirage_backend.main:app --reload
"""

from __future__ import annotations

import httpx
from fastapi import Depends, FastAPI, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session as DBSession

from . import auth, session_service
from .ai_client import AiClient, HttpAiClient
from .config import DEFAULT_CONFIG
from .database import User, make_engine, make_session_factory
from .pdf_service import render_report
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

app = FastAPI(title="Mirage Backend", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

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
    return JSONResponse(
        status_code=502,
        content={"detail": f"AI service unreachable or failing ({type(exc).__name__}): {exc}"},
    )


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


# --- Auth ----------------------------------------------------------------


@app.post("/auth/signup", response_model=TokenResponse)
def signup(payload: SignupRequest, db: DBSession = Depends(get_db)) -> TokenResponse:
    user = auth.signup(db, payload.org_name, payload.email, payload.password)
    token = auth.create_access_token(user, DEFAULT_CONFIG.jwt_secret_key)
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@app.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: DBSession = Depends(get_db)) -> TokenResponse:
    user = auth.login(db, payload.email, payload.password)
    token = auth.create_access_token(user, DEFAULT_CONFIG.jwt_secret_key)
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
def create_session(
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
