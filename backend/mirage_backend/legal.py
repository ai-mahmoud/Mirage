"""Versioned legal-document identifiers.

Document *content* lives in the frontend (frontend/src/features/legal/) —
this module is the single source of truth for the current *version
strings* for each document, so acceptance recorded via POST /consent
always means "the version currently live," not some version that's since
been superseded. Bump the relevant constant here whenever the frontend's
corresponding document's substance changes (a typo fix doesn't need a
version bump; a change to what's actually promised does) — frontend's
`CURRENT_VERSIONS` in src/features/legal/versions.ts must be updated to
match in the same change, or POST /consent will reject the frontend's
now-stale version as `StaleConsentVersion`.
"""

from __future__ import annotations

TERMS_OF_SERVICE_VERSION = "2026-08-13"
PRIVACY_POLICY_VERSION = "2026-08-13"
# The notice shown before a live behavioral session starts — distinct
# from the platform-wide Privacy Policy: this is the specific,
# per-session acknowledgment that behavioral interaction metadata is
# about to be collected (see frontend/src/features/live-session/
# create-session-form.tsx).
SESSION_TRACKING_NOTICE_VERSION = "2026-08-13"

CURRENT_VERSIONS: dict[str, str] = {
    "terms_of_service": TERMS_OF_SERVICE_VERSION,
    "privacy_policy": PRIVACY_POLICY_VERSION,
    "session_tracking_notice": SESSION_TRACKING_NOTICE_VERSION,
}
