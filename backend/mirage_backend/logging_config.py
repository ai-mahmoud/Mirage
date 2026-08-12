"""Structured (JSON) application logging.

Before this, there was zero application-level logging anywhere in
mirage_backend — only uvicorn's default access log. configure_logging()
attaches one JSON-formatted stdout handler to the root logger; every
record picks up the current request's correlation id (see
request_context.py) via RequestIdLogFilter, so `docker compose logs` (or
whatever log aggregator sits in front of it later) can be grepped by
request id across both this service's and ai/'s log streams.
"""

from __future__ import annotations

import json
import logging
import sys

from .request_context import RequestIdLogFilter

_JSON_HANDLER_MARK = "_mirage_json_handler"


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "requestId": getattr(record, "request_id", "-"),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def configure_logging(level: int = logging.INFO) -> None:
    """configure_logging: [int] -> Void
    Purpose: attach the JSON stdout handler to the root logger, unless
    one is already attached (idempotent — safe to call more than once,
    e.g. once per `--reload` worker restart, without stacking up
    duplicate handlers and double-logging every line).
    """
    root = logging.getLogger()
    if any(getattr(h, _JSON_HANDLER_MARK, False) for h in root.handlers):
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    handler.addFilter(RequestIdLogFilter())
    setattr(handler, _JSON_HANDLER_MARK, True)
    root.addHandler(handler)
    root.setLevel(level)
