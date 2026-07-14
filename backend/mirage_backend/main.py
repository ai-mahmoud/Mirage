"""REST API — Mirage Backend.

Thin HTTP layer only: every route validates/parses request data via
schemas.py, then delegates to session_service.py for the actual world-state
transition. Run with:

    uvicorn mirage_backend.main:app --reload
"""

from __future__ import annotations

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session as DBSession

from . import session_service
from .ai_client import AiClient, HttpAiClient
from .config import DEFAULT_CONFIG
from .database import make_engine, make_session_factory
from .pdf_service import render_report
from .schemas import EventBatch, SessionCreate, SessionResponse, TrustStatusResponse

app = FastAPI(title="Mirage Backend", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_engine = make_engine(DEFAULT_CONFIG.database_url)
_session_factory = make_session_factory(_engine)
_ai_client: AiClient = HttpAiClient(DEFAULT_CONFIG.ai_service_url)


def get_db():
    db = _session_factory()
    try:
        yield db
    finally:
        db.close()


def get_ai_client() -> AiClient:
    return _ai_client


def get_reports_dir() -> str:
    return DEFAULT_CONFIG.reports_dir


@app.exception_handler(session_service.SessionNotFound)
def handle_session_not_found(request: Request, exc: session_service.SessionNotFound) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": f"Session not found: {exc}"})


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/sessions", response_model=SessionResponse)
def create_session(
    payload: SessionCreate, db: DBSession = Depends(get_db), ai: AiClient = Depends(get_ai_client)
) -> SessionResponse:
    return session_service.create_session(db, ai, payload)


@app.post("/sessions/{session_id}/events", response_model=TrustStatusResponse)
def post_events(
    session_id: str, batch: EventBatch, db: DBSession = Depends(get_db), ai: AiClient = Depends(get_ai_client)
) -> TrustStatusResponse:
    session_service.record_events(db, ai, session_id, batch.events)
    return session_service.current_status(db, ai, session_id)


@app.get("/sessions/{session_id}/trust", response_model=TrustStatusResponse)
def get_trust(session_id: str, db: DBSession = Depends(get_db), ai: AiClient = Depends(get_ai_client)) -> TrustStatusResponse:
    return session_service.current_status(db, ai, session_id)


@app.post("/sessions/{session_id}/end", response_model=SessionResponse)
def end_session(session_id: str, db: DBSession = Depends(get_db), ai: AiClient = Depends(get_ai_client)) -> SessionResponse:
    return session_service.end_session(db, ai, session_id)


@app.get("/sessions/{session_id}/report")
def get_report(
    session_id: str,
    db: DBSession = Depends(get_db),
    ai: AiClient = Depends(get_ai_client),
    reports_dir: str = Depends(get_reports_dir),
):
    report = session_service.build_report(db, ai, session_id)
    file_path = render_report(report, reports_dir=reports_dir)
    return FileResponse(file_path, media_type="application/pdf", filename=f"session_{session_id}_report.pdf")
