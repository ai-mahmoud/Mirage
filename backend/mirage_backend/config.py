"""Runtime configuration.

Data definition
---------------
A `Config` is a frozen bundle of settings the rest of the service reads:

    ai_service_url  - String, base URL of the ai/ FastAPI process
    database_url    - String, SQLAlchemy database URL
    reports_dir     - String, directory generated PDF reports are written to
    jwt_secret_key  - String, HMAC key signing/verifying auth.py's JWTs
    cors_origins    - (list-of String), browser origins allowed to call this API
    environment     - String, "development" | "production" — gates /docs
                       exposure (see main.py)
    sentry_dsn      - String, Sentry error-tracking DSN; "" (default)
                       disables Sentry entirely — see main.py

Nothing below this module re-reads `os.environ` directly — tests build a
`Config` by hand instead of touching the process environment.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

DEFAULT_CORS_ORIGINS = (
    "http://localhost:5173,http://localhost:3000,https://ai-mahmoud.github.io"
)


def _parse_origins(raw: str) -> list[str]:
    """_parse_origins: String -> (list-of String)
    Purpose: split a comma-separated origins string into a clean list,
    dropping empty entries (a trailing comma or blank env var shouldn't
    produce a `[""]` allowlist that then matches nothing *and* looks
    non-empty).
    """
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


@dataclass(frozen=True)
class Config:
    ai_service_url: str = "http://localhost:8000"
    # Postgres is the real backing store (see docker-compose.yml's postgres
    # service); sqlite is kept only as a fallback for running mirage_backend
    # directly outside docker-compose without standing up Postgres first.
    database_url: str = "postgresql+psycopg://mirage:mirage@localhost:5432/mirage"
    reports_dir: str = "reports"
    # Hackathon-friendly fixed default so tokens survive a dev restart.
    # Production deployments MUST set BACKEND_JWT_SECRET to a real secret
    # (this default is a placeholder, not a claim that it's safe to ship with).
    jwt_secret_key: str = "dev-only-insecure-secret-change-me"
    cors_origins: list[str] = field(default_factory=lambda: _parse_origins(DEFAULT_CORS_ORIGINS))
    environment: str = "development"
    sentry_dsn: str = ""


def load_config() -> Config:
    """load_config: -> Config
    Purpose: build a Config from environment variables, falling back to
    hackathon-friendly local defaults.
    Example:
      with AI_SERVICE_URL unset, load_config().ai_service_url == "http://localhost:8000"
    """
    return Config(
        ai_service_url=os.environ.get("AI_SERVICE_URL", "http://localhost:8000"),
        database_url=os.environ.get(
            "BACKEND_DATABASE_URL", "postgresql+psycopg://mirage:mirage@localhost:5432/mirage"
        ),
        reports_dir=os.environ.get("BACKEND_REPORTS_DIR", "reports"),
        jwt_secret_key=os.environ.get("BACKEND_JWT_SECRET", "dev-only-insecure-secret-change-me"),
        cors_origins=_parse_origins(os.environ.get("BACKEND_CORS_ORIGINS", DEFAULT_CORS_ORIGINS)),
        environment=os.environ.get("BACKEND_ENVIRONMENT", "development"),
        sentry_dsn=os.environ.get("BACKEND_SENTRY_DSN", ""),
    )


DEFAULT_CONFIG = load_config()
