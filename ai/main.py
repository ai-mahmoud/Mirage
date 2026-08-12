"""Entrypoint for FastAPI Cloud (and `fastapi run`).

FastAPI's default app discovery only looks for main.py/app.py/api.py at the
deploy root. The real app lives in mirage_ai/api.py; this just re-exports it.
"""

from mirage_ai.api import app

__all__ = ["app"]
