"""FastAPI surface for the AI stream. This is the contract backend/frontend
teammates integrate against — see ai/README.md. Session state is in-memory
and process-local, which is sufficient for a single-instance hackathon demo.
"""

from __future__ import annotations

import time
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .engine import SessionEngine
from .schemas import (
    CreateSessionRequest,
    CreateSessionResponse,
    IngestRequest,
    SessionReport,
    SessionSnapshot,
)

app = FastAPI(title="Mirage AI", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_sessions: dict[str, SessionEngine] = {}


def _get_session(session_id: str) -> SessionEngine:
    engine = _sessions.get(session_id)
    if engine is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return engine


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/sessions", response_model=CreateSessionResponse)
def create_session(req: CreateSessionRequest) -> CreateSessionResponse:
    session_id = uuid.uuid4().hex
    started_at = time.time() * 1000.0
    _sessions[session_id] = SessionEngine(
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
    return CreateSessionResponse(session_id=session_id, started_at=started_at, demo=req.demo)


@app.post("/sessions/{session_id}/events", response_model=SessionSnapshot)
def ingest_events(session_id: str, req: IngestRequest) -> SessionSnapshot:
    engine = _get_session(session_id)
    engine.ingest(req.events)
    return engine.tick()


@app.get("/sessions/{session_id}", response_model=SessionSnapshot)
def get_session(session_id: str) -> SessionSnapshot:
    return _get_session(session_id).tick()


@app.get("/sessions/{session_id}/report", response_model=SessionReport)
def get_report(session_id: str) -> SessionReport:
    return _get_session(session_id).finalize()


@app.delete("/sessions/{session_id}")
def end_session(session_id: str) -> dict:
    engine = _get_session(session_id)
    del _sessions[session_id]
    return {"status": "deleted", "session_id": engine.session_id}
