// Mirrors backend/mirage_backend/legal.py's CURRENT_VERSIONS exactly.
// Bump the matching constant here in the same change that changes what a
// document actually promises (not for a typo fix) — POST /consent
// rejects a version that doesn't match the backend's as
// StaleConsentVersion.
export const CURRENT_VERSIONS = {
  termsOfService: "2026-08-13",
  privacyPolicy: "2026-08-13",
  sessionTrackingNotice: "2026-08-13",
} as const;

export type ConsentDocument = "terms_of_service" | "privacy_policy" | "session_tracking_notice";
