"""Session-state persistence: SessionStore protocol + implementations.

ai/'s SessionEngine instances used to live only in a process-local dict
(api.py's old `_sessions`) — a restart or horizontal scale-out silently
dropped every live session's evidence. A SessionStore makes that state
durable: PostgresSessionStore round-trips SessionEngine.to_state()/
from_state() (engine.py) through a JSONB column, keyed by session_id.
InMemorySessionStore keeps the original dict-based behavior — used by
ai/'s existing unit tests (test_engine.py, test_features.py, test_seed.py)
so they don't need a database, and available as a local-dev fallback.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Protocol

from sqlalchemy import JSON, Column, DateTime, String, create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

from .engine import SessionEngine

Base = declarative_base()


class SessionRow(Base):
    """One row per session: session_id, its full engine state (to_state()'s
    JSON-safe dict), and when it was last written."""

    __tablename__ = "ai_sessions"

    session_id = Column(String, primary_key=True)
    state = Column(JSON, nullable=False)
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))


class SessionStore(Protocol):
    """A SessionStore is where live SessionEngines live between requests:
        get      : String -> (SessionEngine | None)
        save     : SessionEngine -> Void
        delete   : String -> Void
        list_ids : -> (list-of String)   -- for startup seeding + /seed/sessions
        ping     : -> Boolean             -- for GET /health's readiness check
    """

    def get(self, session_id: str) -> SessionEngine | None: ...

    def save(self, engine: SessionEngine) -> None: ...

    def delete(self, session_id: str) -> None: ...

    def list_ids(self) -> list[str]: ...

    def ping(self) -> bool: ...


class InMemorySessionStore:
    """The original process-dict behavior. Engines are kept as live Python
    objects (no serialize/deserialize round-trip), so this remains what
    ai/'s existing unit tests use — no database dependency."""

    def __init__(self) -> None:
        self._sessions: dict[str, SessionEngine] = {}

    def get(self, session_id: str) -> SessionEngine | None:
        return self._sessions.get(session_id)

    def save(self, engine: SessionEngine) -> None:
        self._sessions[engine.session_id] = engine

    def delete(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    def list_ids(self) -> list[str]:
        return list(self._sessions.keys())

    def ping(self) -> bool:
        return True


class PostgresSessionStore:
    """Durable SessionStore: SessionEngine.to_state() round-tripped through
    a JSON column, keyed by session_id — a process restart re-hydrates
    every live session via from_state() instead of losing it. Works
    against any SQLAlchemy-supported URL (Postgres in prod; a file-backed
    sqlite:/// URL also works, e.g. for a quick local check without
    docker-compose's Postgres service)."""

    def __init__(self, database_url: str) -> None:
        connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
        self._engine = create_engine(database_url, connect_args=connect_args)
        Base.metadata.create_all(bind=self._engine)
        self._session_factory = sessionmaker(autocommit=False, autoflush=False, bind=self._engine)

    def get(self, session_id: str) -> SessionEngine | None:
        with self._session_factory() as db:
            row = db.get(SessionRow, session_id)
            if row is None:
                return None
            return SessionEngine.from_state(row.state)

    def save(self, engine: SessionEngine) -> None:
        state = engine.to_state()
        with self._session_factory() as db:
            row = db.get(SessionRow, engine.session_id)
            if row is None:
                db.add(SessionRow(session_id=engine.session_id, state=state))
            else:
                row.state = state
                row.updated_at = datetime.now(timezone.utc)
            db.commit()

    def delete(self, session_id: str) -> None:
        with self._session_factory() as db:
            row = db.get(SessionRow, session_id)
            if row is not None:
                db.delete(row)
                db.commit()

    def list_ids(self) -> list[str]:
        with self._session_factory() as db:
            return [row.session_id for row in db.query(SessionRow.session_id).all()]

    def ping(self) -> bool:
        with self._session_factory() as db:
            db.execute(text("SELECT 1"))
        return True
