"""FastAPI surface for the AI stream. This is the contract backend/frontend
teammates integrate against — see ai/README.md. Session state is
persisted via a SessionStore (store.py) — a Postgres-backed store in
normal operation, so a restart or scale-out no longer drops live sessions.
"""

from __future__ import annotations

import logging
import time
import uuid

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from .engine import SessionEngine
from .logging_config import configure_logging
from .request_context import RequestIdMiddleware, get_request_id
from .schemas import (
    CreateSessionRequest,
    CreateSessionResponse,
    IngestRequest,
    SeedSessionInfo,
    SessionReport,
    SessionSnapshot,
)
from .seed import PROFILES, seed_sessions
from .settings import DEFAULT_SETTINGS
from .store import PostgresSessionStore, SessionStore

configure_logging()
logger = logging.getLogger("mirage_ai")

if DEFAULT_SETTINGS.sentry_dsn:
    import sentry_sdk

    sentry_sdk.init(
        dsn=DEFAULT_SETTINGS.sentry_dsn, environment=DEFAULT_SETTINGS.environment, traces_sample_rate=0.1
    )

app = FastAPI(
    title="Mirage AI",
    version="0.1.0",
    # /docs, /redoc, and the raw OpenAPI schema are dev conveniences, not
    # something a production deployment should expose to the internet.
    docs_url="/docs" if DEFAULT_SETTINGS.environment != "production" else None,
    redoc_url="/redoc" if DEFAULT_SETTINGS.environment != "production" else None,
    openapi_url="/openapi.json" if DEFAULT_SETTINGS.environment != "production" else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=DEFAULT_SETTINGS.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestIdMiddleware)

# In the real architecture only backend/ creates ai/ sessions
# (server-to-server), but this guards against a misconfigured or
# compromised caller flooding session creation directly.
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Built lazily (on first real get_store() call) rather than at import
# time — importing this module must not require a live database
# connection, since tests override get_store entirely via
# app.dependency_overrides and never invoke this one at all.
_store: SessionStore | None = None


def get_store() -> SessionStore:
    global _store
    if _store is None:
        _store = PostgresSessionStore(DEFAULT_SETTINGS.database_url)
    return _store


@app.on_event("startup")
def _seed_demo_history() -> None:
    """Populate a fresh instance with a handful of realistic finished
    sessions (see seed.py) so backend/'s own seed script has something
    real to mirror — a no-op if the store already has sessions in it.
    seed_sessions() itself is untouched (still builds into a plain dict,
    per its own tests) — we just fan the result out into the real store.
    """
    store = get_store()
    if store.list_ids():
        return
    sessions: dict[str, SessionEngine] = {}
    seed_sessions(sessions)
    for engine in sessions.values():
        store.save(engine)


def _get_session(store: SessionStore, session_id: str) -> SessionEngine:
    engine = store.get(session_id)
    if engine is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return engine


@app.exception_handler(Exception)
def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    # See backend/mirage_backend/main.py's identical handler for why
    # request.state.request_id (not get_request_id()) is used here —
    # FastAPI routes bare-`Exception` handlers outside every
    # add_middleware()-added middleware, including RequestIdMiddleware.
    request_id = getattr(request.state, "request_id", None) or get_request_id()
    logger.exception("unhandled exception")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "requestId": request_id},
        headers={"X-Request-ID": request_id},
    )


@app.get("/health")
def health(store: SessionStore = Depends(get_store)) -> JSONResponse:
    """Liveness AND readiness — a plain "the process is up" response
    can't tell "healthy" from "database unreachable" apart, which is
    useless for orchestration/alerting once this is a real deployment."""
    try:
        store.ping()
        return JSONResponse(status_code=200, content={"status": "ok", "database": "connected"})
    except Exception as exc:  # noqa: BLE001 - any store failure means "not ready"
        logger.error("health check: database unreachable: %s", exc)
        return JSONResponse(status_code=503, content={"status": "degraded", "database": "unreachable"})


@app.post("/sessions", response_model=CreateSessionResponse)
@limiter.limit("60/minute")
def create_session(
    request: Request, req: CreateSessionRequest, store: SessionStore = Depends(get_store)
) -> CreateSessionResponse:
    session_id = uuid.uuid4().hex
    started_at = time.time() * 1000.0
    engine = SessionEngine(
        session_id=session_id,
        candidate_name=req.candidate_name,
        observer_name=req.observer_name,
        position=req.position,
        department=req.department,
        interview_type=req.interview_type,
        demo_mode=req.demo,
        seed=req.seed,
        started_at=started_at,
    )
    store.save(engine)
    return CreateSessionResponse(session_id=session_id, started_at=started_at, demo=req.demo)


@app.post("/sessions/{session_id}/events", response_model=SessionSnapshot)
def ingest_events(
    session_id: str, req: IngestRequest, store: SessionStore = Depends(get_store)
) -> SessionSnapshot:
    engine = _get_session(store, session_id)
    engine.ingest(req.events)
    snapshot = engine.tick()
    store.save(engine)
    return snapshot


@app.get("/sessions/{session_id}", response_model=SessionSnapshot)
def get_session(session_id: str, store: SessionStore = Depends(get_store)) -> SessionSnapshot:
    engine = _get_session(store, session_id)
    snapshot = engine.tick()
    store.save(engine)  # tick() mutates timeline/trust history even on a plain read
    return snapshot


@app.get("/sessions/{session_id}/report", response_model=SessionReport)
def get_report(session_id: str, store: SessionStore = Depends(get_store)) -> SessionReport:
    engine = _get_session(store, session_id)
    report = engine.finalize()
    store.save(engine)
    return report


@app.delete("/sessions/{session_id}")
def end_session(session_id: str, store: SessionStore = Depends(get_store)) -> dict:
    engine = _get_session(store, session_id)
    store.delete(session_id)
    return {"status": "deleted", "session_id": engine.session_id}


@app.get("/seed/sessions", response_model=list[SeedSessionInfo])
def list_seed_sessions(store: SessionStore = Depends(get_store)) -> list[SeedSessionInfo]:
    """Bootstrap-only: the id/identity list for whatever this store
    seeded at startup, so backend/'s own seed script can mirror them
    without hand-duplicating PROFILES. Not part of the product's real
    request-serving contract."""
    seeded_ids = set(store.list_ids())
    return [
        SeedSessionInfo(
            session_id=p["session_id"],
            candidate_name=p["candidate"],
            observer_name=p["observer"],
            position=p["position"],
            department=p["department"],
            interview_type=p["interview_type"],
            live=p["live"],
        )
        for p in PROFILES
        if p["session_id"] in seeded_ids
    ]
