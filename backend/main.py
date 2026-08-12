"""Entrypoint for FastAPI Cloud (and `fastapi run`).

FastAPI's default app discovery only looks for main.py/app.py/api.py at the
deploy root. The real app lives in mirage_backend/main.py; this just
re-exports it.
"""

from mirage_backend.main import app

__all__ = ["app"]
