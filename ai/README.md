# Mirage AI service

Explainable behavioral intelligence engine — the AI stream of the Mirage
hackathon project. FastAPI service; backend and frontend integrate over
this HTTP contract. **Breaking changes here need coordination with both
other teammates.**

Pipeline: `Signal Collection -> Feature Engineering -> Behavior Intelligence
Engine -> Evidence Reasoning Engine -> Trust DNA Generator -> Decision
Confidence Engine -> Human Recommendation Layer`. Rule-based and
deterministic for the MVP (see `mirage_ai/config.py` for every tunable
threshold/weight).

## Run it

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/uvicorn mirage_ai.api:app --reload --port 8000
```

## Privacy

The wire schema (`RawEvent`, see `mirage_ai/schemas.py`) has `extra="forbid"`
and no field that could carry keystroke content, clipboard data, audio, or
video — only event type, timestamp, and (for mouse/scroll) coordinates.

## Endpoints

### `POST /sessions`

Create a session.

```json
// request (all fields optional)
{
  "candidateName": "Demo Candidate",
  "observerName": "Interviewer",
  "position": "Backend Engineer",
  "department": "Engineering",
  "interviewType": "Technical Interview",
  "demo": false,
  "seed": null
}
```

```json
// response
{ "sessionId": "…", "startedAt": 1752500000000.0, "demo": false }
```

`demo: true` self-drives a scripted, deterministic dataset (a natural
baseline, then a "mouse jiggler" event) — no events need to be posted; just
poll the session. Use this as the offline fallback if live tracking is
unstable during the pitch.

### `POST /sessions/{sessionId}/events`

Ingest a batch of raw interaction events; returns the latest snapshot (same
shape as `GET /sessions/{sessionId}`).

```json
{
  "events": [
    { "type": "mouse_move", "t": 1752500001234.0, "x": 512.0, "y": 300.0 },
    { "type": "key_down", "t": 1752500001400.0 },
    { "type": "focus_lost", "t": 1752500002000.0 }
  ]
}
```

`type` is one of: `mouse_move`, `mouse_click`, `scroll` (uses `dy`),
`key_down`, `key_up`, `focus_gained`, `focus_lost`, `visibility_visible`,
`visibility_hidden`. `t` is client epoch-ms (`Date.now()`). Unknown fields
are rejected by the schema.

### `GET /sessions/{sessionId}`

Poll for the live view (recommended: once per second, matching the Live
Session screen's update cadence). Returns a `SessionSnapshot`:

```json
{
  "sessionId": "…",
  "status": "live",
  "startedAt": 1752500000000.0,
  "elapsedMs": 42000.0,
  "trustDna": {
    "dimensions": [
      { "id": "behavioral_consistency", "label": "Behavioral Consistency", "score": 78.4, "confidence": 1.0, "trend": "down" }
    ],
    "overall": 71.2
  },
  "liveSignals": [ /* Signal[] — see below */ ],
  "evidence": [ /* EvidenceCard[], oldest first, accumulates for the session */ ],
  "confidence": { "evidenceConfidence": 0.8, "recommendationConfidence": 0.65, "drivers": ["12/15 signals available"] },
  "recommendation": {
    "status": "additional_observation_recommended",
    "label": "Additional Observation Recommended",
    "reasons": ["…"],
    "suggestedAction": "…",
    "humanReviewRequired": false
  },
  "currentRisk": "elevated",
  "timeline": [ /* TimelineEvent[] */ ]
}
```

`recommendation.status` is one of `continue_monitoring`,
`evidence_insufficient`, `additional_observation_recommended`,
`manual_review_recommended` — deliberately conservative language; the UI
must never render harsher wording than these labels.

`Signal`: `{ signalId, name, category, timestamp, value, normalizedValue,
confidence, reliability, source, context }`. `reliability` is a grade
(`A+`..`D`); render low-grade signals (e.g. `browser_visibility` = `C`) as
supporting evidence only, never as a standalone driver, per the product
constitution.

### `GET /sessions/{sessionId}/report`

Ends analysis and returns the final `SessionReport` for the report/export
screen: executive summary, Trust DNA + history, full evidence table,
recommendation, timeline, and the fixed privacy statement.

### `DELETE /sessions/{sessionId}`

Drop a session from the in-memory store.

### `GET /health`

Liveness check.

## Notes for integrators

- State is in-memory and per-process — restarting the AI service loses all
  sessions. Fine for a single-instance hackathon demo; call out before
  relying on it for anything longer-lived.
- All response bodies are camelCase (the wire format); the Python code
  underneath is snake_case (`alias_generator=to_camel`).
- `min_events_for_analysis` (25) gates everything: below that, every
  endpoint returns `evidence_insufficient` rather than fabricating a
  verdict — this is intentional per the "no conclusion without evidence"
  rule, not a bug.
