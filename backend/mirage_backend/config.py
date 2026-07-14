"""Runtime configuration.

Data definition
---------------
A `Config` is a frozen bundle of settings the rest of the service reads:

    ai_service_url  - String, base URL of the ai/ FastAPI process
    database_url    - String, SQLAlchemy database URL
    reports_dir     - String, directory generated PDF reports are written to

Nothing below this module re-reads `os.environ` directly — tests build a
`Config` by hand instead of touching the process environment.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    ai_service_url: str = "http://localhost:8000"
    database_url: str = "sqlite:///./backend.db"
    reports_dir: str = "reports"


def load_config() -> Config:
    """load_config: -> Config
    Purpose: build a Config from environment variables, falling back to
    hackathon-friendly local defaults.
    Example:
      with AI_SERVICE_URL unset, load_config().ai_service_url == "http://localhost:8000"
    """
    return Config(
        ai_service_url=os.environ.get("AI_SERVICE_URL", "http://localhost:8000"),
        database_url=os.environ.get("BACKEND_DATABASE_URL", "sqlite:///./backend.db"),
        reports_dir=os.environ.get("BACKEND_REPORTS_DIR", "reports"),
    )


DEFAULT_CONFIG = load_config()
