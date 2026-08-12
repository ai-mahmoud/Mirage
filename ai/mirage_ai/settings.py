"""Runtime configuration (env-driven service settings).

Not to be confused with config.py's EngineConfig, which holds the rule
engine's calibrated heuristics (analysis windows, thresholds, weights).
This module mirrors backend/mirage_backend/config.py's Config/load_config
pattern for the small set of settings this *process* needs to start up:

    database_url - String, SQLAlchemy database URL for session persistence

Nothing below this module re-reads `os.environ` directly — tests build a
Settings by hand instead of touching the process environment.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    # Postgres is the real backing store (see docker-compose.yml's postgres
    # service); sqlite is kept only as a fallback for running mirage_ai
    # directly outside docker-compose without standing up Postgres first.
    database_url: str = "postgresql+psycopg://mirage:mirage@localhost:5432/mirage"


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
    )


DEFAULT_SETTINGS = load_settings()
