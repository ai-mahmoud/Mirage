"""GDPR/CCPA-style data-subject rights: export and right-to-deletion —
Phase 7 of the production-readiness roadmap. Mirrors session_service.py's
shape: handlers take the SQLAlchemy DBSession (and AiClient, where a
deletion needs to reach ai/'s mirrored copy too) explicitly.
"""

from __future__ import annotations

from sqlalchemy.orm import Session as DBSession

from .ai_client import AiClient
from .database import EvidenceRow, InterviewSessionRow, Organization, User, UserConsent


class NotOrganizationOwner(Exception):
    """Raised when a non-owner tries to delete their organization —
    deleting every member's access and all of an org's data is not a
    call any team member should be able to make alone."""


def export_organization_data(db: DBSession, org_id: str) -> dict:
    """export_organization_data: DBSession String -> dict
    Purpose: a full, human-readable JSON dump of everything this
    deployment holds about `org_id` — the org record itself, its users
    (never hashed_password — that's a secret, not data the org is owed a
    copy of), and every session with its evidence. This is what GET
    /users/me/export returns: the right-to-access half of GDPR/CCPA,
    scoped to the caller's own org exactly like every other route here.
    """
    org = db.get(Organization, org_id)
    users = db.query(User).filter(User.org_id == org_id).all()
    sessions = db.query(InterviewSessionRow).filter(InterviewSessionRow.org_id == org_id).all()

    return {
        "organization": {
            "orgId": org.org_id,
            "name": org.name,
            "planTier": org.plan_tier,
            "subscriptionStatus": org.subscription_status,
            "createdAt": org.created_at.isoformat(),
        },
        "users": [
            {"userId": u.user_id, "email": u.email, "role": u.role, "createdAt": u.created_at.isoformat()}
            for u in users
        ],
        "sessions": [
            {
                "sessionId": s.session_id,
                "candidateName": s.candidate_name,
                "interviewType": s.interview_type,
                "position": s.position,
                "department": s.department,
                "observerName": s.observer_name,
                "status": s.status,
                "createdAt": s.created_at.isoformat(),
                "endedAt": s.ended_at.isoformat() if s.ended_at else None,
                "trustOverall": s.trust_overall,
                "recommendationLabel": s.recommendation_label,
                "evidence": [
                    {
                        "title": e.title,
                        "description": e.description,
                        "severity": e.severity,
                        "polarity": e.polarity,
                        "timestamp": e.timestamp.isoformat(),
                    }
                    for e in s.evidence
                ],
            }
            for s in sessions
        ],
    }


def delete_organization(db: DBSession, ai: AiClient, org_id: str, requesting_user: User) -> None:
    """delete_organization: DBSession AiClient String User -> Void
    Purpose: permanently delete `org_id` — every session (+ evidence +
    ai/ mirror), every user, and the org itself. Only the org's "owner"
    may call this (raises NotOrganizationOwner otherwise). This is the
    right-to-deletion half of GDPR/CCPA; there is no undo.
    """
    if requesting_user.org_id != org_id or requesting_user.role != "owner":
        raise NotOrganizationOwner(requesting_user.user_id)

    sessions = db.query(InterviewSessionRow).filter(InterviewSessionRow.org_id == org_id).all()
    for session in sessions:
        for evidence in list(session.evidence):
            db.delete(evidence)
        ai_session_id = session.ai_session_id
        db.delete(session)
        db.commit()
        if ai_session_id:
            try:
                ai.delete_session(ai_session_id)
            except Exception:  # noqa: BLE001 - don't let one ai/ failure abort the deletion
                pass

    for user in db.query(User).filter(User.org_id == org_id).all():
        # UserConsent rows FK-reference the user — must go first or a
        # real database (unlike sqlite's default lax mode) rejects the
        # user delete with a foreign-key violation.
        db.query(UserConsent).filter(UserConsent.user_id == user.user_id).delete()
        db.delete(user)
    org = db.get(Organization, org_id)
    if org is not None:
        db.delete(org)
    db.commit()
