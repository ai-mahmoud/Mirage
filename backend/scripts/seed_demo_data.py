"""One-time demo-data seeder.

Mirrors the ai/ service's own seeded demo history (see
ai/mirage_ai/seed.py) into the backend's database, over the exact same
HttpAiClient proxy path the real runtime uses (mirage_backend.ai_client +
mirage_backend.session_service) — this script does not import ai/'s code
at all. It requires the ai/ service to already be reachable and to have
already seeded itself, hence the retry loop below.

PROFILES here must reference the same session ids ai/'s seed.py uses —
those are the only thing duplicated between the two; everything else
(trust scores, evidence, timing) is derived from ai/'s real response.

Run with (from backend/, with backend/.venv activated and ai/ running):
    python scripts/seed_demo_data.py
"""

from __future__ import annotations

import sys
import time
import uuid
from datetime import datetime, timezone

from mirage_backend import session_service
from mirage_backend.ai_client import HttpAiClient
from mirage_backend.config import DEFAULT_CONFIG
from mirage_backend.database import InterviewSessionRow, make_engine, make_session_factory

# Must match ai/mirage_ai/seed.py's PROFILES' session ids and identity fields.
PROFILES = [
    ("seed-amara-osei", "Amara Osei", "Backend Engineer", "Engineering", "Technical Interview", "Priya Raman"),
    ("seed-diego-fernandez", "Diego Fernandez", "Frontend Engineer", "Engineering", "Technical Interview", "Priya Raman"),
    ("seed-mei-lin-tan", "Mei Lin Tan", "Data Analyst", "Data", "Screening Call", "Jordan Blake"),
    ("seed-samuel-okafor", "Samuel Okafor", "Product Manager", "Product", "Panel Interview", "Jordan Blake"),
    ("seed-nour-el-sayed", "Nour El-Sayed", "Site Reliability Engineer", "Engineering", "Technical Interview", "Priya Raman"),
    ("seed-elena-popescu", "Elena Popescu", "UX Designer", "Design", "Portfolio Review", "Jordan Blake"),
]


def _wait_for_ai(ai: HttpAiClient, session_id: str, retries: int, delay_s: float) -> None:
    """_wait_for_ai: HttpAiClient String Number Number -> Void
    Purpose: block until ai/'s seeded `session_id` is reachable, or raise
    once `retries` is exhausted. ai/ seeds itself at its own startup, but
    container start order isn't the same as "app ready."
    """
    for attempt in range(retries):
        try:
            ai.get_snapshot(session_id)
            return
        except Exception:  # noqa: BLE001 - genuinely any failure means "not ready yet"
            if attempt == retries - 1:
                raise
            time.sleep(delay_s)


def seed(db_url: str, ai_service_url: str, retries: int = 30, delay_s: float = 2.0) -> None:
    """seed: String String [Number] [Number] -> Void
    Purpose: populate `db_url` by mirroring ai/'s seeded sessions, unless
    it already has data (idempotent — safe to call on every container start).
    """
    engine_db = make_engine(db_url)
    factory = make_session_factory(engine_db)
    db = factory()
    ai = HttpAiClient(ai_service_url, timeout=10.0)
    try:
        if db.query(InterviewSessionRow).first() is not None:
            print("Database already has data — skipping seed.")
            return

        print(f"Waiting for ai/ service at {ai_service_url} to be seeded...")
        _wait_for_ai(ai, PROFILES[0][0], retries, delay_s)

        for ai_session_id, candidate, position, department, interview_type, observer in PROFILES:
            row = InterviewSessionRow(
                session_id=str(uuid.uuid4()),
                ai_session_id=ai_session_id,
                candidate_name=candidate,
                interview_type=interview_type,
                position=position,
                department=department,
                observer_name=observer,
            )
            db.add(row)
            db.commit()
            db.refresh(row)

            snapshot = ai.get_snapshot(ai_session_id)
            session_service.apply_snapshot(db, row, snapshot)
            row.created_at = datetime.fromtimestamp(snapshot["startedAt"] / 1000.0, tz=timezone.utc)
            if snapshot["status"] == "ended":
                row.status = "ended"
                row.ended_at = datetime.fromtimestamp(
                    (snapshot["startedAt"] + snapshot["elapsedMs"]) / 1000.0, tz=timezone.utc
                )
                report = ai.get_report(ai_session_id)
                row.executive_summary = report["executiveSummary"]
            db.commit()

            print(f"  seeded {candidate!r} ({row.status}) -> trust {row.trust_overall:.1f}, "
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
