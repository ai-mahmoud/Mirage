"""Data-retention purge — Phase 7 of the production-readiness roadmap.

Deletes every session (across all orgs) older than BACKEND_RETENTION_DAYS
(default 90) and its mirrored ai/ copy. Meant to be run periodically, not
from a request handler — see .github/workflows/purge-expired-sessions.yml
for the free (GitHub Actions' scheduled-workflow) way this repo runs it,
since the deployment stays off any paid cron infra for now.

Run with (from backend/, with backend/.venv activated):
    python scripts/purge_expired_sessions.py
"""

from __future__ import annotations

import sys

from mirage_backend import session_service
from mirage_backend.ai_client import HttpAiClient
from mirage_backend.config import DEFAULT_CONFIG
from mirage_backend.database import make_engine, make_session_factory


def main() -> None:
    engine = make_engine(DEFAULT_CONFIG.database_url)
    factory = make_session_factory(engine)
    db = factory()
    ai = HttpAiClient(DEFAULT_CONFIG.ai_service_url)
    try:
        count = session_service.purge_expired_sessions(db, ai, DEFAULT_CONFIG.retention_days)
        print(f"Purged {count} session(s) older than {DEFAULT_CONFIG.retention_days} days.")
    finally:
        db.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001
        print(f"Purge failed: {exc}", file=sys.stderr)
        sys.exit(1)
