"""Runtime configuration (env-driven service settings).

Not to be confused with config.py's EngineConfig, which holds the rule
engine's calibrated heuristics (analysis windows, thresholds, weights).
This module mirrors backend/mirage_backend/config.py's Config/load_config
pattern for the small set of settings this *process* needs to start up:

    database_url - String, SQLAlchemy database URL for session persistence
    cors_origins - (list-of String), browser origins allowed to call this
                    API directly. In the real architecture only backend/
                    talks to ai/ (server-to-server, no Origin header, so
                    CORS doesn't even apply) — this exists for local
                    direct-testing convenience, not because browsers are
                    meant to hit ai/ in production.
    environment  - String, "development" | "production" — gates /docs
                    exposure (see api.py)
    sentry_dsn   - String, Sentry error-tracking DSN; "" (default)
                    disables Sentry entirely — see api.py

Nothing below this module re-reads `os.environ` directly — tests build a
Settings by hand instead of touching the process environment.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

DEFAULT_CORS_ORIGINS = "http://localhost:8001"


def _parse_origins(raw: str) -> list[str]:
    """_parse_origins: String -> (list-of String)
    Purpose: split a comma-separated origins string into a clean list,
    dropping empty entries.
    """
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


@dataclass(frozen=True)
class Settings:
    # Postgres is the real backing store (see docker-compose.yml's postgres
    # service); sqlite is kept only as a fallback for running mirage_ai
    # directly outside docker-compose without standing up Postgres first.
    database_url: str = "postgresql+psycopg://mirage:mirage@localhost:5432/mirage"
    cors_origins: list[str] = field(default_factory=lambda: _parse_origins(DEFAULT_CORS_ORIGINS))
    environment: str = "development"
    sentry_dsn: str = ""


def load_settings() -> Settings:
    """load_settings: -> Settings
    Purpose: build a Settings from environment variables, falling back to
    hackathon-friendly local defaults.
    Example:
      with AI_DATABASE_URL set to "sqlite:///./ai.db", load_settings().database_url == "sqlite:///./ai.db"
    """
    return Settings(
        database_url=os.environ.get(
            "AI_DATABASE_URL", "postgresql+psycopg://mirage:mirage@localhost:5432/mirage"
        ),
        cors_origins=_parse_origins(os.environ.get("AI_CORS_ORIGINS", DEFAULT_CORS_ORIGINS)),
        environment=os.environ.get("AI_ENVIRONMENT", "development"),
        sentry_dsn=os.environ.get("AI_SENTRY_DSN", ""),
    )


DEFAULT_SETTINGS = load_settings()
