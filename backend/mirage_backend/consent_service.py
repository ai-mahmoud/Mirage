"""Consent world-state transitions — Phase 7 of the production-readiness
roadmap (see /home/dr4who/.claude/plans/tidy-spinning-babbage.md).

World data definition
----------------------
A User's consent state is the set of UserConsent rows recorded for them
(database.py) — never updated in place, only inserted, so there's always
a full acceptance history. Mirrors session_service.py's shape: handlers
take the SQLAlchemy DBSession explicitly, no module-level globals.
"""

from __future__ import annotations

from sqlalchemy.orm import Session as DBSession

from .database import UserConsent, new_id
from .legal import CURRENT_VERSIONS


class UnknownDocument(Exception):
    """Raised when `document` isn't one of legal.CURRENT_VERSIONS' keys."""


class StaleConsentVersion(Exception):
    """Raised when a client tries to record acceptance of a version that
    isn't the current one — accepting an old version isn't meaningful
    consent to today's document. The client is expected to always send
    legal.CURRENT_VERSIONS[document]; seeing anything else means the
    frontend build is stale relative to the backend it's talking to."""


class ConsentRequired(Exception):
    """Raised by session_service.create_session when the caller hasn't
    accepted the current session_tracking_notice version yet."""


def record_consent(db: DBSession, user_id: str, document: str, version: str) -> UserConsent:
    """record_consent: DBSession String String String -> UserConsent
    Purpose: record that `user_id` accepted `version` of `document`,
    which must be the current version (see legal.py). Idempotent in
    effect (recording the same current version twice just adds a second
    identical row) rather than raising — a duplicate accept click isn't
    an error.
    """
    current = CURRENT_VERSIONS.get(document)
    if current is None:
        raise UnknownDocument(document)
    if version != current:
        raise StaleConsentVersion(f"{document} current version is {current!r}, got {version!r}")

    row = UserConsent(id=new_id(), user_id=user_id, document=document, version=version)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def has_current_consent(db: DBSession, user_id: str, document: str) -> bool:
    """has_current_consent: DBSession String String -> Boolean
    Purpose: has `user_id` accepted the *current* version of `document`?
    An acceptance of a since-superseded version doesn't count.
    """
    current = CURRENT_VERSIONS.get(document)
    if current is None:
        return False
    return (
        db.query(UserConsent)
        .filter(UserConsent.user_id == user_id, UserConsent.document == document, UserConsent.version == current)
        .first()
        is not None
    )


def consent_status(db: DBSession, user_id: str) -> dict[str, bool]:
    """consent_status: DBSession String -> (dict String -> Boolean)
    Purpose: has_current_consent for every known document at once — what
    the frontend polls to decide which consent gates still need showing.
    """
    return {document: has_current_consent(db, user_id, document) for document in CURRENT_VERSIONS}
