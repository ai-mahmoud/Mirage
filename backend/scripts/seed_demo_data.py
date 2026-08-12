"""One-time demo-data seeder.

Mirrors the ai/ service's own seeded demo history (see
ai/mirage_ai/seed.py) into the backend's database, over the exact same
HttpAiClient proxy path the real runtime uses (mirage_backend.ai_client +
mirage_backend.session_service) — this script does not import ai/'s code
at all. The list of what to mirror comes from ai/'s bootstrap-only
GET /seed/sessions endpoint, so nothing here duplicates ai/'s PROFILES.

Run with (from backend/, with backend/.venv activated and ai/ running):
    python scripts/seed_demo_data.py
"""

from __future__ import annotations

import sys
import time
from datetime import datetime, timezone

import httpx

from mirage_backend import session_service
from mirage_backend.ai_client import HttpAiClient
from mirage_backend.config import DEFAULT_CONFIG
from mirage_backend.database import InterviewSessionRow, make_engine, make_session_factory


def _wait_for_seed_list(ai_service_url: str, retries: int, delay_s: float) -> list[dict]:
    """_wait_for_seed_list: String Number Number -> (list-of dict)
    Purpose: block until ai/'s GET /seed/sessions returns a non-empty list,
    or raise once `retries` is exhausted. ai/ seeds itself at its own
    startup, but container start order isn't the same as "app ready."
    """
    for attempt in range(retries):
        try:
            resp = httpx.get(f"{ai_service_url}/seed/sessions", timeout=10.0)
            resp.raise_for_status()
            entries = resp.json()
            if entries:
                return entries
        except Exception:  # noqa: BLE001 - genuinely any failure means "not ready yet"
            pass
        if attempt == retries - 1:
            raise RuntimeError(f"ai/ service at {ai_service_url} never returned a seed list")
        time.sleep(delay_s)
    return []  # unreachable, satisfies type-checkers


def seed(db_url: str, ai_service_url: str, retries: int = 60, delay_s: float = 2.0) -> None:
    """seed: String String [Number] [Number] -> Void
    Purpose: populate `db_url` by mirroring every session ai/ seeded
    itself with, unless the database already has data (idempotent — safe
    to call on every container start).
    """
    engine_db = make_engine(db_url)
    factory = make_session_factory(engine_db)
    db = factory()
    ai = HttpAiClient(ai_service_url, timeout=10.0)
    try:
        if db.query(InterviewSessionRow).first() is not None:
            print("Database already has data — skipping seed.")
            return

        print(f"Waiting for ai/ service at {ai_service_url} to finish seeding itself...")
        entries = _wait_for_seed_list(ai_service_url, retries, delay_s)
        print(f"Mirroring {len(entries)} seeded sessions...")

        for entry in entries:
            ai_session_id = entry["sessionId"]
            row = InterviewSessionRow(
                ai_session_id=ai_session_id,
                candidate_name=entry["candidateName"],
                interview_type=entry["interviewType"] or "Technical Interview",
                position=entry["position"],
                department=entry["department"],
                observer_name=entry["observerName"],
            )
            db.add(row)
            db.commit()
            db.refresh(row)

            snapshot = ai.get_snapshot(ai_session_id)
            session_service.apply_snapshot(db, row, snapshot)
            row.created_at = datetime.fromtimestamp(snapshot["startedAt"] / 1000.0, tz=timezone.utc)

            if not entry["live"]:
                row.status = "ended"
                row.ended_at = datetime.fromtimestamp(
                    (snapshot["startedAt"] + snapshot["elapsedMs"]) / 1000.0, tz=timezone.utc
                )
                report = ai.get_report(ai_session_id)
                row.executive_summary = report["executiveSummary"]
            db.commit()

            print(f"  seeded {entry['candidateName']!r} ({row.status}) -> trust {row.trust_overall:.1f}, "
                  f"{len(row.evidence)} evidence item(s)")
    finally:
        db.close()


if __name__ == "__main__":
    try:
        seed(DEFAULT_CONFIG.database_url, DEFAULT_CONFIG.ai_service_url)
    except Exception as exc:  # noqa: BLE001
        print(f"Seeding failed: {exc}", file=sys.stderr)
        print("Continuing without demo data — the app still works, just starts empty.", file=sys.stderr)
    print("Done.")
