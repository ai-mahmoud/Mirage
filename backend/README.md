# Mirage backend

Session persistence, PDF export, and the HTTP proxy to the [ai/](../ai)
evidence-synthesis service. This service holds **no** behavioral-intelligence
logic of its own — that lives entirely in `ai/`, so there is one pipeline
and one source of truth for Trust DNA. The backend's job is:

1. Forward each client's raw interaction-event batch to `ai/` verbatim.
2. Mirror the resulting Trust DNA / evidence / recommendation into its own
   database (so the Live Session and Report screens don't have to hit
   `ai/` on every read, and history survives an `ai/` restart).
3. Persist session records (candidate, observer, position, department).
4. Render the final Session Report as a PDF.

## Layout

Written to follow the *How to Design Programs* recipes throughout: every
data type has an interpretation comment above its definition, and every
function has a signature comment, a purpose statement, and (where useful)
a worked example in its docstring — see any module for the pattern.

| File | Responsibility |
|---|---|
| `config.py` | environment-derived settings (`Config`) |
| `database.py` | SQLAlchemy data definitions + engine/session-factory construction |
| `schemas.py` | wire-format (Pydantic) data definitions |
| `ai_client.py` | the `AiClient` interface + `HttpAiClient`, the only place that talks to `ai/` |
| `session_service.py` | world-state transitions — the actual request handlers, independent of FastAPI |
| `pdf_service.py` | pure report-row builders + `render_report` |
| `main.py` | thin FastAPI routing layer; every route is one line of delegation |

`main.py` never contains business logic — if you're adding a rule about
*when* something happens, it belongs in `session_service.py`, not a route.

## Run it

Needs the `ai/` service running too (default `http://localhost:8000`):

```bash
# terminal 1
cd ../ai && .venv/bin/uvicorn mirage_ai.api:app --port 8000

# terminal 2
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
AI_SERVICE_URL=http://localhost:8000 .venv/bin/uvicorn mirage_backend.main:app --reload --port 8001
```

Environment variables (all optional, see `config.py`):

| Variable | Default |
|---|---|
| `AI_SERVICE_URL` | `http://localhost:8000` |
| `BACKEND_DATABASE_URL` | `sqlite:///./backend.db` |
| `BACKEND_REPORTS_DIR` | `reports` |

## Tests

```bash
.venv/bin/pytest
```

Tests never require a live `ai/` process:
- `test_ai_client.py` drives `HttpAiClient` against `httpx.MockTransport`.
- `test_session_service.py` / `test_main_api.py` use `tests/fakes.py`'s
  `FakeAiClient` plus an in-memory SQLite database.
- `test_pdf_service.py` tests the row-builder functions directly, and
  separately confirms `render_report` produces a real PDF file.

## Endpoints

| Method | Path | Delegates to |
|---|---|---|
| `POST` | `/sessions` | `session_service.create_session` |
| `POST` | `/sessions/{id}/events` | `session_service.record_events` + `current_status` |
| `GET` | `/sessions/{id}/trust` | `session_service.current_status` |
| `POST` | `/sessions/{id}/end` | `session_service.end_session` |
| `GET` | `/sessions/{id}/report` | `session_service.build_report` + `pdf_service.render_report` |
| `GET` | `/health` | liveness check |

Request/response payloads mirror `ai/README.md`'s contract — `POST
/sessions/{id}/events` takes the same raw event batch shape (`type`, `t`,
`x`, `y`, `dy`) that `ai/` expects, forwarded through unchanged. A missing
`session_id` on any route returns `404` via a single exception handler
(`session_service.SessionNotFound`), not a scattered `if row is None` in
every route.

## Notes for integrators

- This is a rewrite of the original placeholder backend: it no longer has
  its own rule-based trust engine (`trust_engine.py` is gone) and the
  `/sessions/{id}/signals` endpoint (abstracted, pre-computed feature
  values) is replaced by `/sessions/{id}/events` (raw interaction
  metadata, forwarded to `ai/` for feature engineering). If any client
  code already targets the old shape, it needs to send raw events instead.
- `ai_session_id` is an internal implementation detail — clients only ever
  see the backend's own `session_id`.
